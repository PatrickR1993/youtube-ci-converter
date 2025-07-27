#!/usr/bin/env python3
"""
Translation interface module
Handles audio translation workflow with progress tracking.
"""

import os
import sys
from pathlib import Path


def run_translation_with_progress(translator, input_file, output_dir, progress_tracker, separate_files=False, use_parallel=True, merge_segments=True):
    """Run audio translation with progress tracking.
    
    Args:
        translator: AudioTranslator instance
        input_file: Path to input audio file
        output_dir: Output directory for processed files
        progress_tracker: Progress tracking instance
        separate_files: Whether to keep files separate
        use_parallel: Whether to use parallel processing for translation and TTS (much faster)
        merge_segments: Whether to merge short Whisper segments into longer sentences
    """
    try:
        # Extract sentences with Whisper (0-30% of translation step)
        sentences = translator.extract_sentences_whisper(input_file, progress_tracker, merge_segments=merge_segments)
        
        if not sentences:
            return False
        
        # Translate sentences (30-100% of translation step)
        if use_parallel:
            # Use parallel translation (much faster for multiple sentences)
            translated_sentences = translator.translate_sentences_parallel(sentences, progress_tracker)
        else:
            # Use sequential translation (original method)
            translated_sentences = translator.translate_sentences(sentences, progress_tracker)
            
        progress_tracker.update_step('translation', 100, "Translation complete")
        
        if not translated_sentences:
            return False
        
        # Start audio generation phase (now with parallel TTS)
        progress_tracker.update_step('audio_gen', 0, "Generating bilingual audio with parallel TTS")
        
        # Create bilingual audio with progress updates (now uses parallel TTS internally)
        output_file = translator.create_bilingual_audio_with_progress(
            input_file, translated_sentences, output_dir, progress_tracker, separate_files
        )
        
        if output_file:
            progress_tracker.update_step('audio_gen', 100, "Audio generation complete")
            return output_file  # Return the actual output file path
        else:
            return None
            
    except Exception as e:
        print(f"Translation error: {e}")
        return None


def get_audio_translator_class():
    """Import and return the AudioTranslator class."""
    try:
        # Try to import from current directory first (for backward compatibility)
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from audio_translator import AudioTranslator
        return AudioTranslator
    except ImportError:
        try:
            # Try to import from src directory
            from audio_translator import AudioTranslator
            return AudioTranslator
        except ImportError:
            print("❌ Could not import audio_translator module")
            print("   Make sure audio_translator.py is in the project directory")
            return None
