#!/usr/bin/env python3
"""
AI Audio Translator for Japanese Podcasts
Analyzes Japanese audio, translates to English, and creates bilingual audio
"""

import os
import sys
import json
import time
import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Tuple
import argparse

try:
    import openai
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    import tempfile
except ImportError as e:
    missing_package = str(e).split("'")[1] if "'" in str(e) else str(e)
    print(f"Error: Required package '{missing_package}' is not installed.")
    print("Please install required packages using:")
    print("pip install openai pydub")
    print("Also install system dependencies:")
    print("- Ubuntu/Debian: sudo apt install ffmpeg")
    print("- macOS: brew install ffmpeg")
    sys.exit(1)

# Import utility functions
try:
    from utils import sanitize_filename
except ImportError:
    # Fallback if utils module is not available
    def sanitize_filename(filename):
        """Fallback function to sanitize filenames."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip('. ')[:100]


class AudioTranslator:
    """Main class for handling Japanese audio translation."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the audio translator.
        
        Args:
            openai_api_key: OpenAI API key for Whisper, GPT translation, and TTS
        """
        self.openai_client = None
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
        
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def _split_audio_file(self, audio_file: Path, temp_dir: Path) -> tuple[Path, Path]:
        """Split an audio file into two equal halves.
        
        Args:
            audio_file: Path to the audio file to split
            temp_dir: Directory to store temporary split files
            
        Returns:
            Tuple of (first_half_path, second_half_path, split_time_ms)
        """
        try:
            # Load audio file
            audio = AudioSegment.from_file(str(audio_file))
            duration = len(audio)  # Duration in milliseconds
            
            # Split into two halves
            first_half = audio[:duration // 2]
            second_half = audio[duration // 2:]
            
            # Create temporary file paths
            base_name = audio_file.stem
            first_half_path = temp_dir / f"{base_name}_part1.mp3"
            second_half_path = temp_dir / f"{base_name}_part2.mp3"
            
            # Export both halves
            first_half.export(str(first_half_path), format="mp3")
            second_half.export(str(second_half_path), format="mp3")
            
            return first_half_path, second_half_path, duration // 2
            
        except Exception as e:
            print(f"❌ Failed to split audio file: {e}")
            raise

    def _merge_segments_into_sentences(self, segments: List[Dict], max_gap_seconds: float = 2.0, min_sentence_length: int = 20) -> List[Dict]:
        """Merge short Whisper segments into longer, more natural sentences.
        
        Args:
            segments: List of segment dictionaries from Whisper
            max_gap_seconds: Maximum gap between segments to merge (default: 2 seconds)
            min_sentence_length: Minimum characters for a sentence before forcing a split
            
        Returns:
            List of merged sentence dictionaries
        """
        if not segments:
            return []
        
        merged_sentences = []
        current_sentence = {
            "text": "",
            "start_time": segments[0]["start_time"],
            "end_time": segments[0]["end_time"]
        }
        
        for i, segment in enumerate(segments):
            segment_text = segment["text"].strip()
            
            # Skip empty segments
            if not segment_text:
                continue
            
            # Check if we should start a new sentence
            should_split = False
            
            if current_sentence["text"]:  # Not the first segment
                # Calculate gap between current sentence end and this segment start
                gap = segment["start_time"] - current_sentence["end_time"]
                
                # Split conditions:
                # 1. Long pause (more than max_gap_seconds)
                # 2. Previous text ends with sentence-ending punctuation
                # 3. Current sentence is getting very long (over 200 characters)
                # 4. Segment starts with capital letter after some content exists
                
                prev_text = current_sentence["text"].rstrip()
                
                if (gap >= max_gap_seconds or 
                    prev_text.endswith(('。', '！', '？', '.', '!', '?')) or
                    len(current_sentence["text"]) > 200 or
                    (len(current_sentence["text"]) > min_sentence_length and 
                     segment_text and segment_text[0].isupper() and 
                     gap > 0.8)):  # Shorter gap threshold for capital letters
                    
                    should_split = True
            
            if should_split and current_sentence["text"].strip():
                # Finalize current sentence
                merged_sentences.append(current_sentence.copy())
                
                # Start new sentence
                current_sentence = {
                    "text": segment_text,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"]
                }
            else:
                # Merge with current sentence
                if current_sentence["text"]:
                    # Add appropriate spacing
                    if (current_sentence["text"].rstrip().endswith(('、', ',')) or 
                        segment_text.startswith(('、', ','))):
                        # No extra space needed for comma continuation
                        current_sentence["text"] += segment_text
                    else:
                        # Add space between segments
                        current_sentence["text"] += " " + segment_text
                else:
                    current_sentence["text"] = segment_text
                    current_sentence["start_time"] = segment["start_time"]
                
                # Update end time
                current_sentence["end_time"] = segment["end_time"]
        
        # Add the final sentence
        if current_sentence["text"].strip():
            merged_sentences.append(current_sentence)
        
        return merged_sentences

    def _extract_sentences_whisper_single(self, audio_file: Path, time_offset: float = 0.0, merge_segments: bool = True) -> List[Dict]:
        """Extract sentences from a single audio file using Whisper API.
        
        Args:
            audio_file: Path to the audio file
            time_offset: Time offset to add to all timestamps (for split files)
            merge_segments: Whether to merge short segments into longer sentences
            
        Returns:
            List of dictionaries with text, start_time, end_time
        """
        try:
            with open(audio_file, "rb") as audio:
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="ja",  # Japanese
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            segments = []
            for i, segment in enumerate(response.segments):
                try:
                    # Try attribute access first (newer OpenAI library)
                    text = segment.text.strip()
                    start_time = segment.start + time_offset
                    end_time = segment.end + time_offset
                    
                    if text:  # Only add non-empty segments
                        segments.append({
                            "text": text,
                            "start_time": start_time,
                            "end_time": end_time
                        })
                    
                except AttributeError:
                    # Fallback to dictionary access (older format)
                    try:
                        text = segment["text"].strip()
                        start_time = segment["start"] + time_offset
                        end_time = segment["end"] + time_offset
                        
                        if text:  # Only add non-empty segments
                            segments.append({
                                "text": text,
                                "start_time": start_time,
                                "end_time": end_time
                            })
                        
                    except (KeyError, TypeError) as e:
                        print(f"⚠️  Could not parse segment {i}: {e}")
                        continue
            
            # Merge segments into longer sentences if requested
            if merge_segments and segments:
                sentences = self._merge_segments_into_sentences(segments)
                print(f"📝 Merged {len(segments)} segments into {len(sentences)} longer sentences")
                return sentences
            else:
                return segments
            
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {e}")

    def extract_sentences_whisper(self, audio_file: Path, progress_tracker=None, max_splits: int = 4, current_split: int = 0, merge_segments: bool = True) -> List[Dict]:
        """Extract Japanese sentences using OpenAI Whisper API with recursive splitting on failure.
        
        Args:
            audio_file: Path to the audio file
            progress_tracker: Optional UnifiedProgressTracker for progress updates
            max_splits: Maximum number of recursive splits (4 times = 16 segments max)
            current_split: Current split level (internal use)
            merge_segments: Whether to merge short segments into longer sentences (default: True)
            
        Returns:
            List of dictionaries with text, start_time, end_time
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key required for Whisper transcription")
            
        # Update progress tracker on first call
        if current_split == 0 and progress_tracker:
            progress_tracker.update_step('translation', 0, "Starting audio transcription")
        
        # Get file size for user feedback
        file_size = audio_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Try transcribing the file directly
        try:
            if progress_tracker and current_split == 0:
                progress_tracker.update_step('translation', 10, f"Transcribing audio ({file_size_mb:.1f}MB)")
            elif current_split > 0:
                print(f"🔄 Attempting transcription of split {current_split + 1} ({file_size_mb:.1f}MB)")
                
            sentences = self._extract_sentences_whisper_single(audio_file, 0.0, merge_segments)
            
            # Update progress after successful transcription
            if progress_tracker and current_split == 0:
                progress_tracker.update_step('translation', 30, f"Extracted {len(sentences)} Japanese sentences")
            elif current_split > 0:
                print(f"✅ Successfully transcribed split {current_split + 1}: {len(sentences)} sentences")
            
            return sentences
            
        except Exception as e:
            # If we've reached max splits, give up
            if current_split >= max_splits:
                print(f"❌ Whisper transcription failed after {max_splits} splits: {e}")
                if "file size" in str(e).lower() or "too large" in str(e).lower():
                    print("💡 Tip: Try converting your audio to a lower bitrate or shorter duration")
                return []
            
            # Try splitting the file and processing recursively
            print(f"⚠️  Whisper failed (attempt {current_split + 1}): {e}")
            print(f"🔄 Splitting audio file and retrying... (split {current_split + 1}/{max_splits})")
            
            try:
                # Create temporary directory for splits
                import tempfile
                temp_dir = Path(tempfile.mkdtemp(prefix="whisper_split_"))
                
                try:
                    # Split the audio file
                    first_half_path, second_half_path, split_time_ms = self._split_audio_file(audio_file, temp_dir)
                    split_time_seconds = split_time_ms / 1000.0
                    
                    if progress_tracker and current_split == 0:
                        progress_tracker.update_step('translation', 15, f"File too large, splitting into segments (attempt {current_split + 1})")
                    
                    # Recursively process both halves
                    first_sentences = self.extract_sentences_whisper(
                        first_half_path, 
                        progress_tracker=None,  # Don't update progress for sub-calls
                        max_splits=max_splits, 
                        current_split=current_split + 1,
                        merge_segments=merge_segments
                    )
                    
                    second_sentences = self.extract_sentences_whisper(
                        second_half_path, 
                        progress_tracker=None,  # Don't update progress for sub-calls
                        max_splits=max_splits, 
                        current_split=current_split + 1,
                        merge_segments=merge_segments
                    )
                    
                    # Adjust timestamps for second half
                    for sentence in second_sentences:
                        sentence["start_time"] += split_time_seconds
                        sentence["end_time"] += split_time_seconds
                    
                    # Combine results
                    all_sentences = first_sentences + second_sentences
                    
                    if progress_tracker and current_split == 0:
                        progress_tracker.update_step('translation', 30, f"Successfully split and transcribed: {len(all_sentences)} sentences total")
                    
                    print(f"✅ Successfully processed split audio: {len(all_sentences)} total sentences")
                    return all_sentences
                    
                finally:
                    # Clean up temporary files
                    try:
                        if first_half_path.exists():
                            first_half_path.unlink()
                        if second_half_path.exists():
                            second_half_path.unlink()
                        temp_dir.rmdir()
                    except Exception as cleanup_error:
                        print(f"⚠️  Warning: Could not clean up temporary files: {cleanup_error}")
                        
            except Exception as split_error:
                print(f"❌ Failed to split audio file: {split_error}")
                return []
    
    def translate_sentences(self, sentences: List[Dict], progress_tracker=None) -> List[Dict]:
        """Translate Japanese sentences to English.
        
        Args:
            sentences: List of sentence dictionaries
            progress_tracker: Optional UnifiedProgressTracker for progress updates
            
        Returns:
            List of sentences with English translations added
        """
        total_sentences = len(sentences)
        
        for i, sentence in enumerate(sentences):
            japanese_text = sentence["text"]
            
            try:
                if self.openai_client:
                    # Use GPT for high-quality translation
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a professional Japanese to English translator. Translate the following Japanese text to natural, fluent English. Preserve the meaning and tone. Only return the translation, no explanations."
                            },
                            {
                                "role": "user", 
                                "content": japanese_text
                            }
                        ],
                        max_tokens=200,
                        temperature=0.3
                    )
                    english_text = response.choices[0].message.content.strip()
                else:
                    # Fallback: Use a simple translation service or placeholder
                    english_text = f"[Translation of: {japanese_text[:50]}...]"
                
                sentence["english"] = english_text
                
                # Update unified progress tracker if provided
                if progress_tracker:
                    # Translation is 30-100% of translation step (70% total)
                    translation_progress = 30 + ((i + 1) / total_sentences) * 70
                    progress_tracker.update_step('translation', translation_progress, f"Translating {i+1}/{total_sentences}")
                
                # Small delay to avoid rate limiting
                if self.openai_client:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"⚠️  Translation failed for sentence {i+1}: {e}")
                sentence["english"] = f"[Translation failed: {japanese_text}]"
        
        return sentences
    
    def translate_single_sentence(self, sentence_data: Tuple[int, Dict]) -> Tuple[int, Dict]:
        """Translate a single sentence - designed for parallel execution.
        
        Args:
            sentence_data: Tuple of (index, sentence_dict)
            
        Returns:
            Tuple of (index, updated_sentence_dict)
        """
        i, sentence = sentence_data
        japanese_text = sentence["text"]
        
        try:
            if self.openai_client:
                # Use GPT for high-quality translation
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional Japanese to English translator. Translate the following Japanese text to natural, fluent English. Preserve the meaning and tone. Only return the translation, no explanations."
                        },
                        {
                            "role": "user", 
                            "content": japanese_text
                        }
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                english_text = response.choices[0].message.content.strip()
            else:
                # Fallback: Use a simple translation service or placeholder
                english_text = f"[Translation of: {japanese_text[:50]}...]"
            
            sentence["english"] = english_text
            return i, sentence
            
        except Exception as e:
            print(f"⚠️  Translation failed for sentence {i+1}: {e}")
            sentence["english"] = f"[Translation failed: {japanese_text}]"
            return i, sentence
    
    def translate_sentences_parallel(self, sentences: List[Dict], progress_tracker=None, max_workers: int = 20) -> List[Dict]:
        """Translate all sentences in parallel for much faster processing.
        
        Args:
            sentences: List of sentence dictionaries
            progress_tracker: Optional UnifiedProgressTracker for progress updates
            max_workers: Maximum number of concurrent translation requests (increased for better performance)
            
        Returns:
            List of sentences with English translations added
        """
        total_sentences = len(sentences)
        
        # Prepare data for parallel processing
        sentence_data = [(i, sentence.copy()) for i, sentence in enumerate(sentences)]
        
        if progress_tracker:
            progress_tracker.update_step('translation', 30, f"Starting parallel translation of {total_sentences} sentences")
        
        # Use ThreadPoolExecutor for parallel API calls
        translated_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all translation tasks
            future_to_index = {
                executor.submit(self.translate_single_sentence, data): data[0] 
                for data in sentence_data
            }
            
            # Process completed translations
            completed = 0
            for future in concurrent.futures.as_completed(future_to_index):
                try:
                    index, translated_sentence = future.result()
                    translated_results[index] = translated_sentence
                    completed += 1
                    
                    # Update progress
                    if progress_tracker:
                        translation_progress = 30 + (completed / total_sentences) * 70
                        progress_tracker.update_step('translation', translation_progress, f"Translated {completed}/{total_sentences}")
                        
                except Exception as e:
                    index = future_to_index[future]
                    print(f"⚠️  Translation failed for sentence {index+1}: {e}")
                    # Keep original sentence with failed translation marker
                    translated_results[index] = sentences[index].copy()
                    translated_results[index]["english"] = f"[Translation failed: {sentences[index]['text']}]"
                    completed += 1
        
        # Rebuild sentences list in original order
        result_sentences = []
        for i in range(total_sentences):
            if i in translated_results:
                result_sentences.append(translated_results[i])
            else:
                # Fallback for any missing translations
                fallback = sentences[i].copy()
                fallback["english"] = f"[Translation missing: {sentences[i]['text']}]"
                result_sentences.append(fallback)
        
        return result_sentences
    
    def generate_english_audio_for_sentence(self, sentence_data: Tuple[int, str, Path]) -> Tuple[int, bool, Path]:
        """Generate English audio for a single sentence - designed for parallel execution.
        
        Args:
            sentence_data: Tuple of (index, english_text, output_file_path)
            
        Returns:
            Tuple of (index, success_bool, output_file_path)
        """
        i, text, output_file = sentence_data
        
        try:
            if self.openai_client:
                # Generate speech using OpenAI TTS
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text,
                    response_format="mp3"
                )
                
                # Save audio to file
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                return i, True, output_file
            else:
                print(f"⚠️  No OpenAI client available for TTS")
                return i, False, output_file
                
        except Exception as e:
            print(f"⚠️  TTS generation failed for sentence {i+1}: {e}")
            return i, False, output_file
    
    def generate_english_audio(self, text: str, output_file: Path) -> bool:
        """Generate English speech audio from text using OpenAI TTS.
        
        Args:
            text: English text to convert to speech
            output_file: Path to save the audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized - API key required")
                
            # Use OpenAI TTS for natural speech
            with self.openai_client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",  # Natural female voice
                input=text
            ) as response:
                response.stream_to_file(str(output_file))
            return True
        except Exception as e:
            print(f"⚠️  OpenAI TTS failed for text: {text[:50]}... Error: {e}")
            return False
    
    def create_bilingual_audio(self, original_audio: Path, sentences: List[Dict], output_file: Path) -> bool:
        """Create bilingual audio with English before Japanese.
        
        Args:
            original_audio: Path to original Japanese audio
            sentences: List of translated sentences with timing
            output_file: Path to save the bilingual audio
            
        Returns:
            True if successful, False otherwise
        """
        print("🎵 Creating bilingual audio...")
        
        try:
            # Load original audio
            original = AudioSegment.from_file(str(original_audio))
            bilingual_audio = AudioSegment.empty()
            
            last_end_time = 0
            total_segments = len(sentences)
            
            print(f"🎵 Creating bilingual audio ({total_segments} segments)...")
            
            for i, sentence in enumerate(sentences):
                start_ms = int(sentence["start_time"] * 1000)
                end_ms = int(sentence["end_time"] * 1000)
                
                # Add any gap between sentences from original
                if start_ms > last_end_time:
                    gap = original[last_end_time:start_ms]
                    bilingual_audio += gap
                
                # Generate English audio
                english_file = self.temp_dir / f"english_{i}.mp3"
                if self.generate_english_audio(sentence["english"], english_file):
                    english_audio = AudioSegment.from_file(str(english_file))
                    
                    # Add English translation
                    bilingual_audio += english_audio
                    
                    # Add small pause
                    bilingual_audio += AudioSegment.silent(duration=300)  # 300ms pause
                    
                    # Clean up temp file
                    english_file.unlink()
                
                # Add original Japanese segment
                japanese_segment = original[start_ms:end_ms]
                bilingual_audio += japanese_segment
                
                # Add pause after Japanese
                bilingual_audio += AudioSegment.silent(duration=500)  # 500ms pause
                
                last_end_time = end_ms
                
                # Simple progress indicator
                if (i + 1) % 5 == 0 or (i + 1) == total_segments:
                    print(f"   Processed {i + 1}/{total_segments} segments...")
            
            # Add any remaining audio
            if last_end_time < len(original):
                remaining = original[last_end_time:]
                bilingual_audio += remaining
            
            # Export final bilingual audio
            bilingual_audio.export(str(output_file), format="mp3")
            print(f"✅ Bilingual audio saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create bilingual audio: {e}")
            return False
        finally:
            # Clean up temp directory
            for temp_file in self.temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except:
                    pass
    
    def create_bilingual_audio_with_progress(self, original_audio: Path, sentences: List[Dict], output_dir: Path, progress_tracker, separate_files: bool = False) -> Path:
        """Create bilingual audio with progress tracking integration and parallel TTS generation.
        
        Args:
            original_audio: Path to original Japanese audio
            sentences: List of translated sentences with timing
            output_dir: Directory to save the bilingual audio
            progress_tracker: UnifiedProgressTracker instance
            separate_files: Whether to keep files separate or create combined version
            
        Returns:
            Path to output file if successful, None otherwise
        """
        try:
            # Load original audio
            original = AudioSegment.from_file(str(original_audio))
            total_segments = len(sentences)
            
            # Step 1: Generate all English audio files in parallel
            progress_tracker.update_step('audio_gen', 10, f"Generating {total_segments} English audio files in parallel")
            
            # Prepare data for parallel TTS generation
            tts_data = []
            english_files = {}
            for i, sentence in enumerate(sentences):
                english_file = self.temp_dir / f"english_{i}.mp3"
                english_files[i] = english_file
                tts_data.append((i, sentence["english"], english_file))
            
            # Generate all English audio in parallel (much faster!)
            tts_results = {}
            max_tts_workers = 20  # Increased TTS workers for maximum parallel processing

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_tts_workers) as executor:
                # Submit all TTS tasks
                future_to_index = {
                    executor.submit(self.generate_english_audio_for_sentence, data): data[0] 
                    for data in tts_data
                }
                
                # Process completed TTS generations
                completed_tts = 0
                for future in concurrent.futures.as_completed(future_to_index):
                    try:
                        index, success, file_path = future.result()
                        tts_results[index] = success
                        completed_tts += 1
                        
                        # Update progress (10-60% for TTS generation)
                        tts_progress = 10 + (completed_tts / total_segments) * 50
                        progress_tracker.update_step('audio_gen', tts_progress, f"Generated TTS {completed_tts}/{total_segments}")
                        
                    except Exception as e:
                        index = future_to_index[future]
                        print(f"⚠️  TTS generation failed for sentence {index+1}: {e}")
                        tts_results[index] = False
                        completed_tts += 1
            
            # Step 2: Assemble the final bilingual audio
            progress_tracker.update_step('audio_gen', 60, "Assembling bilingual audio from generated segments")
            
            bilingual_audio = AudioSegment.empty()
            last_end_time = 0
            
            for i, sentence in enumerate(sentences):
                start_ms = int(sentence["start_time"] * 1000)
                end_ms = int(sentence["end_time"] * 1000)
                
                # Add any gap between sentences from original
                if start_ms > last_end_time:
                    gap = original[last_end_time:start_ms]
                    bilingual_audio += gap
                
                # Add English audio (if generation was successful)
                if tts_results.get(i, False) and english_files[i].exists():
                    try:
                        english_audio = AudioSegment.from_file(str(english_files[i]))
                        bilingual_audio += english_audio
                        bilingual_audio += AudioSegment.silent(duration=300)  # 300ms pause
                    except Exception as e:
                        print(f"⚠️  Could not load English audio for sentence {i+1}: {e}")
                        # Continue without English audio for this segment
                
                # Add original Japanese segment
                japanese_segment = original[start_ms:end_ms]
                bilingual_audio += japanese_segment
                
                # Add pause after Japanese
                bilingual_audio += AudioSegment.silent(duration=500)  # 500ms pause
                
                last_end_time = end_ms
                
                # Update assembly progress (60-90%)
                assembly_progress = 60 + ((i + 1) / total_segments) * 30
                progress_tracker.update_step('audio_gen', assembly_progress, f"Assembling segment {i+1}/{total_segments}")
            
            # Add any remaining audio
            if last_end_time < len(original):
                remaining = original[last_end_time:]
                bilingual_audio += remaining
            
            # Export bilingual audio
            bilingual_file = output_dir / f"{original_audio.stem}_bilingual.mp3"
            bilingual_audio.export(str(bilingual_file), format="mp3")
            
            # Clean up temporary English audio files
            for english_file in english_files.values():
                try:
                    if english_file.exists():
                        english_file.unlink()
                except:
                    pass
            
            if separate_files:
                # Keep files separate - return the bilingual file
                progress_tracker.update_step('audio_gen', 100, "Bilingual audio complete")
                output_file = bilingual_file
            else:
                # Create combined audio: bilingual + audio cue + original
                progress_tracker.update_step('audio_gen', 90, "Creating combined audio with original")
                
                # Create a more noticeable audio cue
                # 1 second of silence + short beep tone + 1 second of silence
                audio_cue = AudioSegment.silent(duration=1000)  # 1 second silence
                
                # Create a simple beep using sine wave (440Hz for 0.5 seconds)
                try:
                    from pydub.generators import Sine
                    beep = Sine(440).to_audio_segment(duration=500)  # 440Hz for 0.5 seconds
                    beep = beep - 20  # Reduce volume by 20dB to make it gentle
                    audio_cue += beep + AudioSegment.silent(duration=1000)  # beep + 1 second silence
                except ImportError:
                    # Fallback: just use 2.5 seconds of silence if pydub.generators is not available
                    audio_cue += AudioSegment.silent(duration=1500)  # 1.5 more seconds of silence
                
                # Load the original audio again for the final section
                original_full = AudioSegment.from_file(str(original_audio))
                
                # Combine: bilingual + audio cue + original
                combined_audio = bilingual_audio + audio_cue + original_full
                
                # Export combined audio
                combined_file = output_dir / f"{original_audio.stem}_complete.mp3"
                combined_audio.export(str(combined_file), format="mp3")
                
                # Remove the separate bilingual file since we have the combined version
                if bilingual_file.exists():
                    bilingual_file.unlink()
                
                # Remove the original audio file since it's included in the combined version
                if original_audio.exists():
                    original_audio.unlink()
                
                progress_tracker.update_step('audio_gen', 100, "Combined audio complete")
                output_file = combined_file
            
            # Save transcript
            transcript_file = output_dir / f"{original_audio.stem}_transcript.json"
            self.save_transcript(sentences, transcript_file)
            
            return output_file
            
        except Exception as e:
            print(f"❌ Failed to create bilingual audio: {e}")
            return None
        finally:
            # Clean up temp directory
            for temp_file in self.temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except:
                    pass
    
    def save_transcript(self, sentences: List[Dict], output_file: Path):
        """Save the transcript with translations to a JSON file.
        
        Args:
            sentences: List of translated sentences
            output_file: Path to save the transcript
        """
        transcript_data = {
            "metadata": {
                "total_sentences": len(sentences),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "sentences": sentences
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up temporary directory: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


def find_mp3_files(directory: Path) -> List[Path]:
    """Find all MP3 files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of MP3 file paths
    """
    if not directory.exists():
        return []
    
    return list(directory.glob("*.mp3"))


def main():
    """Main function for the audio translator."""
    parser = argparse.ArgumentParser(
        description="Translate Japanese audio to English and create bilingual audio",
        epilog="Example: python audio_translator.py --file podcast.mp3 --api-key your_openai_key\n\n"
               "Output: Creates files in ./output/Local Files/ containing:\n"
               "  - Original MP3 file\n"
               "  - JSON transcript file\n"
               "  - Bilingual MP3 file",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--file', '-f',
        help='Specific MP3 file to translate'
    )
    parser.add_argument(
        '--api-key',
        help='OpenAI API key for Whisper and GPT (required for operation)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for translated files (default: ./output/)'
    )
    
    args = parser.parse_args()
    
    print("🎌 YouTube CI Converter")
    print("=" * 50)
    
    # Get OpenAI API key (required)
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key is required for operation.")
        print("   Provide an API key with --api-key")
        print("   Or set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    # Initialize translator
    translator = AudioTranslator(api_key)
    
    print("🎤 Using OpenAI TTS for natural-sounding English speech")
    
    # Get input file
    if args.file:
        input_file = Path(args.file)
        if not input_file.exists():
            print(f"❌ File not found: {input_file}")
            sys.exit(1)
    else:
        # Look for MP3 files in downloads directory
        downloads_dir = Path("downloads")
        mp3_files = find_mp3_files(downloads_dir)
        
        if not mp3_files:
            print("❌ No MP3 files found in downloads directory.")
            print("   Use --file to specify a specific MP3 file")
            sys.exit(1)
        
        print("📁 Found MP3 files:")
        for i, file in enumerate(mp3_files, 1):
            print(f"   {i}. {file.name}")
        
        while True:
            try:
                choice = input(f"\nSelect file (1-{len(mp3_files)}): ").strip()
                file_index = int(choice) - 1
                if 0 <= file_index < len(mp3_files):
                    input_file = mp3_files[file_index]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(mp3_files)}")
            except ValueError:
                print("Please enter a valid number")
    
    # Set up output directory with channel structure
    if args.output_dir:
        base_output_dir = Path(args.output_dir)
    else:
        base_output_dir = Path("output")
    
    base_output_dir.mkdir(exist_ok=True)
    
    # Create channel directory for standalone audio files
    channel_name = "Local Files"
    sanitized_channel = sanitize_filename(channel_name)
    channel_output_dir = base_output_dir / sanitized_channel
    channel_output_dir.mkdir(exist_ok=True)
    
    # Generate output filenames in channel directory
    base_name = input_file.stem
    bilingual_file = channel_output_dir / f"{base_name}_bilingual.mp3"
    transcript_file = channel_output_dir / f"{base_name}_transcript.json"
    
    print(f"\n🎯 Processing: {input_file.name}")
    print(f"📂 Channel: {channel_name}")
    print(f"📤 Output directory: {channel_output_dir}")
    
    try:
        # Step 1: Extract sentences with timing using Whisper
        sentences = translator.extract_sentences_whisper(input_file)
        
        if not sentences:
            print("❌ No sentences could be extracted from the audio")
            sys.exit(1)
        
        # Step 2: Translate sentences
        translated_sentences = translator.translate_sentences(sentences)
        
        # Step 3: Save transcript
        translator.save_transcript(translated_sentences, transcript_file)
        
        # Step 4: Create bilingual audio
        success = translator.create_bilingual_audio(
            input_file, 
            translated_sentences, 
            bilingual_file
        )
        
        if success:
            print(f"\n🎉 Translation completed successfully!")
            print(f"📄 Transcript: {transcript_file}")
            print(f"🎵 Bilingual audio: {bilingual_file}")
            print(f"\n💡 The bilingual audio contains:")
            print(f"   - English translation (spoken)")
            print(f"   - Original Japanese (from source)")
            print(f"   - Pattern: EN → JP → EN → JP...")
        else:
            print("\n❌ Translation failed")
            sys.exit(1)
    
    finally:
        # Clean up temporary files
        translator.cleanup()


if __name__ == "__main__":
    main()
