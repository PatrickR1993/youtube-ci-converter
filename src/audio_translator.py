#!/usr/bin/env python3
"""
AI Audio Translator for Japanese Podcasts
Analyzes Japanese audio, translates to English, and creates bilingual audio
"""

import os
import sys
import json
import time
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
        
    def _estimate_chunk_size(self, chunk_duration_ms: int, bytes_per_ms: float) -> float:
        """Estimate the file size of a chunk in MB.
        
        Args:
            chunk_duration_ms: Duration of chunk in milliseconds
            bytes_per_ms: Estimated bytes per millisecond from original file
            
        Returns:
            Estimated size in MB
        """
        estimated_bytes = chunk_duration_ms * bytes_per_ms
        return estimated_bytes / (1024 * 1024)
    
    def _get_safe_chunk_duration(self, audio_file: Path, audio_duration_ms: int) -> int:
        """Calculate a safe chunk duration to stay under API limits.
        
        Args:
            audio_file: Path to the original audio file
            audio_duration_ms: Total duration in milliseconds
            
        Returns:
            Safe chunk duration in milliseconds
        """
        original_file_size = audio_file.stat().st_size
        bytes_per_ms = original_file_size / audio_duration_ms
        
        # Target 18MB per chunk to stay well under 26MB limit
        target_chunk_size = 18 * 1024 * 1024
        optimal_chunk_duration_ms = int(target_chunk_size / bytes_per_ms)
        
        # Ensure chunks are between 3-6 minutes for safety and efficiency
        min_chunk_duration = 3 * 60 * 1000   # 3 minutes
        max_chunk_duration = 6 * 60 * 1000   # 6 minutes
        
        return max(min_chunk_duration, min(optimal_chunk_duration_ms, max_chunk_duration))
        
    def extract_sentences_whisper(self, audio_file: Path, progress_tracker=None) -> List[Dict]:
        """Extract Japanese sentences using OpenAI Whisper API.
        
        Args:
            audio_file: Path to the audio file
            progress_tracker: Optional UnifiedProgressTracker for progress updates
            
        Returns:
            List of dictionaries with text, start_time, end_time
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key required for Whisper transcription")
            
        # Update progress tracker
        if progress_tracker:
            progress_tracker.update_step('translation', 0, "Checking audio file size")
        
        # Check file size and chunk if necessary (OpenAI has ~26MB limit)
        file_size = audio_file.stat().st_size
        max_size = 20 * 1024 * 1024  # 20MB to be very safe (was 25MB)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size > max_size:
            if progress_tracker:
                progress_tracker.update_step('translation', 5, f"Large file ({file_size_mb:.1f}MB) - will process in chunks")
            return self._transcribe_large_audio(audio_file, progress_tracker)
        
        try:
            if progress_tracker:
                progress_tracker.update_step('translation', 10, f"Transcribing audio ({file_size_mb:.1f}MB)")
                
            with open(audio_file, "rb") as audio:
                # Use Whisper API for transcription with timestamps
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="ja",  # Japanese
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Update progress after API call
            if progress_tracker:
                progress_tracker.update_step('translation', 15, f"Transcription complete - processing {len(response.segments)} segments")
            
            sentences = []
            for i, segment in enumerate(response.segments):
                try:
                    # Try attribute access first (newer OpenAI library)
                    text = segment.text.strip()
                    start_time = segment.start
                    end_time = segment.end
                    
                    sentences.append({
                        "text": text,
                        "start_time": start_time,
                        "end_time": end_time
                    })
                    
                except AttributeError:
                    # Fallback to dictionary access (older format)
                    try:
                        text = segment["text"].strip()
                        start_time = segment["start"]
                        end_time = segment["end"]
                        
                        sentences.append({
                            "text": text,
                            "start_time": start_time,
                            "end_time": end_time
                        })
                        
                    except (KeyError, TypeError) as e:
                        print(f"⚠️  Could not parse segment {i}: {e}")
                        print(f"   Segment type: {type(segment)}")
                        print(f"   Segment content: {segment}")
                        
                        # Try getattr as last resort
                        try:
                            text = getattr(segment, 'text', '') or str(segment)
                            start_time = getattr(segment, 'start', i * 10)  # Estimate timing
                            end_time = getattr(segment, 'end', (i + 1) * 10)
                            
                            if text.strip():
                                sentences.append({
                                    "text": text.strip(),
                                    "start_time": start_time,
                                    "end_time": end_time
                                })
                        except Exception as final_err:
                            print(f"   Final fallback failed: {final_err}")
                            continue
            
            # Update progress tracker
            if progress_tracker:
                progress_tracker.update_step('translation', 30, f"Extracted {len(sentences)} Japanese sentences")
            
            return sentences
            
        except Exception as e:
            print(f"❌ Whisper transcription failed: {e}")
            return []
    
    def _transcribe_large_audio(self, audio_file: Path, progress_tracker=None) -> List[Dict]:
        """Transcribe large audio files by chunking them into smaller pieces.
        
        Args:
            audio_file: Path to the large audio file
            progress_tracker: Optional UnifiedProgressTracker for progress updates
            
        Returns:
            List of dictionaries with text, start_time, end_time (merged from all chunks)
        """
        try:
            # Load the audio file
            if progress_tracker:
                progress_tracker.update_step('translation', 5, "Loading audio file for chunking")
            
            audio = AudioSegment.from_file(audio_file)
            
            # Calculate optimal chunk duration using utility function
            total_duration_ms = len(audio)
            chunk_duration_ms = self._get_safe_chunk_duration(audio_file, total_duration_ms)
            
            # Estimate chunk sizes for user feedback
            original_file_size = audio_file.stat().st_size
            bytes_per_ms = original_file_size / total_duration_ms
            estimated_chunk_size_mb = self._estimate_chunk_size(chunk_duration_ms, bytes_per_ms)
            
            chunks = []
            total_duration = len(audio)
            num_chunks = (total_duration + chunk_duration_ms - 1) // chunk_duration_ms  # Ceiling division
            
            if progress_tracker:
                progress_tracker.update_step('translation', 10, f"Splitting into {num_chunks} chunks (~{estimated_chunk_size_mb:.1f}MB each)")
            
            # Split audio into chunks
            for i in range(0, total_duration, chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]
                chunk_start_time = i / 1000.0  # Convert to seconds
                chunks.append((chunk, chunk_start_time))
            
            all_sentences = []
            
            # Process each chunk with size validation
            for chunk_idx, (chunk, chunk_start_time) in enumerate(chunks):
                if progress_tracker:
                    chunk_progress = 15 + (chunk_idx / len(chunks)) * 70  # 15-85% for chunk processing
                    progress_tracker.update_step('translation', chunk_progress, 
                                                f"Transcribing chunk {chunk_idx + 1}/{len(chunks)}")
                
                # Export chunk to temporary file
                chunk_file = self.temp_dir / f"chunk_{chunk_idx}.wav"
                chunk.export(chunk_file, format="wav")
                
                # Validate chunk size before sending to API
                chunk_size = chunk_file.stat().st_size
                chunk_size_mb = chunk_size / (1024 * 1024)
                max_size_mb = 25  # Stay under 26MB limit
                
                if chunk_size > max_size_mb * 1024 * 1024:
                    print(f"⚠️  Chunk {chunk_idx + 1} is {chunk_size_mb:.1f}MB (over {max_size_mb}MB limit)")
                    
                    # If chunk is still too large, use recursive splitting
                    if chunk_size > 26 * 1024 * 1024:  # Over hard limit
                        print(f"🔄 Splitting chunk {chunk_idx + 1} recursively into smaller pieces...")
                        
                        # Use recursive splitting to handle extremely large chunks
                        sub_sentences = self._split_and_transcribe_chunk(
                            chunk, chunk_start_time, chunk_idx, max_size_bytes=25 * 1024 * 1024
                        )
                        all_sentences.extend(sub_sentences)
                        
                        # Clean up main chunk file
                        if chunk_file.exists():
                            chunk_file.unlink()
                        continue
                
                try:
                    # Transcribe this chunk
                    with open(chunk_file, "rb") as audio_chunk:
                        response = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_chunk,
                            language="ja",  # Japanese
                            response_format="verbose_json",
                            timestamp_granularities=["segment"]
                        )
                    
                    # Process segments and adjust timestamps
                    for segment in response.segments:
                        try:
                            # Try attribute access first (newer OpenAI library)
                            text = segment.text.strip()
                            start_time = segment.start + chunk_start_time
                            end_time = segment.end + chunk_start_time
                            
                            if text:  # Only add non-empty segments
                                all_sentences.append({
                                    "text": text,
                                    "start_time": start_time,
                                    "end_time": end_time
                                })
                                
                        except AttributeError:
                            # Fallback to dictionary access
                            try:
                                text = segment["text"].strip()
                                start_time = segment["start"] + chunk_start_time
                                end_time = segment["end"] + chunk_start_time
                                
                                if text:
                                    all_sentences.append({
                                        "text": text,
                                        "start_time": start_time,
                                        "end_time": end_time
                                    })
                                    
                            except (KeyError, TypeError):
                                print(f"⚠️  Could not parse segment in chunk {chunk_idx}")
                                continue
                
                except Exception as e:
                    print(f"⚠️  Failed to transcribe chunk {chunk_idx + 1}: {e}")
                    continue
                
                finally:
                    # Clean up temporary chunk file
                    if chunk_file.exists():
                        chunk_file.unlink()
                
                # Small delay between API calls
                time.sleep(0.5)
            
            if progress_tracker:
                progress_tracker.update_step('translation', 90, f"Merged {len(all_sentences)} segments from {len(chunks)} chunks")
            
            return all_sentences
            
        except Exception as e:
            print(f"❌ Large audio transcription failed: {e}")
            return []
    
    def _split_and_transcribe_chunk(self, chunk: AudioSegment, chunk_start_time: float, 
                                  chunk_idx: int, max_size_bytes: int = 25 * 1024 * 1024,
                                  recursion_depth: int = 0) -> List[Dict]:
        """Recursively split and transcribe a chunk that's too large for the API.
        
        Args:
            chunk: AudioSegment that needs to be split
            chunk_start_time: Start time offset for this chunk in seconds
            chunk_idx: Index of the parent chunk (for naming)
            max_size_bytes: Maximum allowed size in bytes
            recursion_depth: Current recursion depth (for safety)
            
        Returns:
            List of transcribed sentences with correct timestamps
        """
        # Safety check to prevent infinite recursion
        if recursion_depth > 5:
            print(f"⚠️  Maximum recursion depth reached for chunk {chunk_idx}. Skipping...")
            return []
        
        # Also check minimum chunk size - if chunk is too small, skip it
        if len(chunk) < 1000:  # Less than 1 second
            print(f"⚠️  Chunk {chunk_idx} too small ({len(chunk)}ms). Skipping...")
            return []
        
        sentences = []
        
        # Export chunk to check its size
        temp_file = self.temp_dir / f"temp_chunk_{chunk_idx}_check.wav"
        chunk.export(temp_file, format="wav")
        chunk_size = temp_file.stat().st_size
        
        if chunk_size <= max_size_bytes:
            # Chunk is small enough, transcribe it
            try:
                with open(temp_file, "rb") as audio_chunk:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_chunk,
                        language="ja",
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                
                # Process segments with adjusted timestamps
                for segment in response.segments:
                    try:
                        text = segment.text.strip()
                        start_time = segment.start + chunk_start_time
                        end_time = segment.end + chunk_start_time
                        
                        if text:
                            sentences.append({
                                "text": text,
                                "start_time": start_time,
                                "end_time": end_time
                            })
                    except (AttributeError, KeyError, TypeError):
                        continue
                        
            except Exception as e:
                print(f"⚠️  Failed to transcribe chunk: {e}")
            finally:
                if temp_file.exists():
                    temp_file.unlink()
        else:
            # Chunk is still too large, split it further
            chunk_size_mb = chunk_size / (1024 * 1024)
            print(f"   🔄 Chunk still {chunk_size_mb:.1f}MB, splitting further...")
            
            # Split into smaller pieces (aim for 4 pieces to be more aggressive)
            quarter_duration = len(chunk) // 4
            sub_chunks = [
                (chunk[0:quarter_duration], 0),
                (chunk[quarter_duration:2*quarter_duration], quarter_duration),
                (chunk[2*quarter_duration:3*quarter_duration], 2*quarter_duration),
                (chunk[3*quarter_duration:], 3*quarter_duration)
            ]
            
            # Recursively process each sub-chunk
            for i, (sub_chunk, offset_ms) in enumerate(sub_chunks):
                if len(sub_chunk) > 0:  # Skip empty chunks
                    offset_seconds = offset_ms / 1000.0
                    sub_sentences = self._split_and_transcribe_chunk(
                        sub_chunk, 
                        chunk_start_time + offset_seconds, 
                        f"{chunk_idx}_{i}",
                        max_size_bytes,
                        recursion_depth + 1
                    )
                    sentences.extend(sub_sentences)
        
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
            
        return sentences

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
        """Create bilingual audio with progress tracking integration.
        
        Args:
            original_audio: Path to original Japanese audio
            sentences: List of translated sentences with timing
            output_dir: Directory to save the bilingual audio
            progress_tracker: UnifiedProgressTracker instance
            
        Returns:
            Path to output file if successful, None otherwise
        """
        try:
            # Create output filename
            output_file = output_dir / f"{original_audio.stem}_bilingual.mp3"
            
            # Load original audio
            original = AudioSegment.from_file(str(original_audio))
            bilingual_audio = AudioSegment.empty()
            
            last_end_time = 0
            total_segments = len(sentences)
            
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
                
                # Update progress
                segment_progress = ((i + 1) / total_segments) * 100
                progress_tracker.update_step('audio_gen', segment_progress, f"Generating segment {i+1}/{total_segments}")
            
            # Add any remaining audio
            if last_end_time < len(original):
                remaining = original[last_end_time:]
                bilingual_audio += remaining
            
            # Export bilingual audio
            bilingual_file = output_dir / f"{original_audio.stem}_bilingual.mp3"
            bilingual_audio.export(str(bilingual_file), format="mp3")
            
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
