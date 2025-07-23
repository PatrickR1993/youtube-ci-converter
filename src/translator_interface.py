#!/usr/bin/env python3
"""
Translation interface module
Handles audio translation workflow with progress tracking.
"""

import os
import sys
from pathlib import Path


def run_translation_with_progress(translator, input_file, output_dir, progress_tracker, separate_files=False):
    """Run audio translation with progress tracking."""
    try:
        # Extract sentences with Whisper (0-30% of translation step)
        sentences = translator.extract_sentences_whisper(input_file, progress_tracker)
        
        if not sentences:
            return False
        
        # Translate sentences with GPT (30-100% of translation step)  
        translated_sentences = translator.translate_sentences(sentences, progress_tracker)
        progress_tracker.update_step('translation', 100, "Translation complete")
        
        if not translated_sentences:
            return False
        
        # Start audio generation phase
        progress_tracker.update_step('audio_gen', 0, "Generating bilingual audio")
        
        # Create bilingual audio with progress updates
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
