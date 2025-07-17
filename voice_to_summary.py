# Realistic Toastmasters Transcript Summarizer
# Works with raw Whisper output - no timestamps, no speaker labels, no guaranteed keywords

import os
import glob
import re
import json
from datetime import datetime
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig
)
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # Model settings
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    MAX_CHUNK_SIZE = 4000  # Smaller chunks for better processing
    OVERLAP_SIZE = 400     # Decent overlap to maintain context
    MAX_SUMMARY_LENGTH = 600
    
    # File paths
    INPUT_FOLDER = "/kaggle/input/toastmasters-transcripts"
    OUTPUT_FOLDER = "/kaggle/working/summaries"
    
    # Model settings
    USE_4BIT = True
    TEMPERATURE = 0.3  # Lower for more consistent summaries

# ============================================================================
# SETUP AND MODEL LOADING
# ============================================================================

def setup_environment():
    """Install required packages and setup directories"""
    print("Setting up environment...")
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    print("✓ Environment setup complete")

def load_model():
    """Load Llama 3.1 8B model with quantization"""
    print("Loading Llama 3.1 8B model (this may take a few minutes)...")
    
    # Quantization config
    if Config.USE_4BIT:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
    else:
        quantization_config = None
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(Config.MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        Config.MODEL_NAME,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    
    print("✓ Model loaded successfully")
    print(f"✓ Model device: {model.device}")
    return model, tokenizer

# ============================================================================
# TEXT PROCESSING
# ============================================================================

def clean_whisper_transcript(text):
    """Clean raw Whisper output - minimal cleaning to preserve content"""
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common Whisper artifacts if present
    text = re.sub(r'\[MUSIC\]|\[APPLAUSE\]|\[LAUGHTER\]|\[NOISE\]', '', text)
    text = re.sub(r'\[.*?\]', '', text)  # Any bracketed content
    
    # Clean up extra spaces and newlines
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def smart_chunk_text(text, max_chunk_size=Config.MAX_CHUNK_SIZE, overlap_size=Config.OVERLAP_SIZE):
    """
    Intelligently chunk text by trying to break at natural boundaries
    """
    # Rough token estimation (1 token ≈ 0.75 words)
    words = text.split()
    words_per_chunk = int(max_chunk_size * 0.75)
    overlap_words = int(overlap_size * 0.75)
    
    if len(words) <= words_per_chunk:
        return [text]  # Single chunk if small enough
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        
        # Try to find a natural break point in the last 10% of the chunk
        if end < len(words):  # Not the last chunk
            break_zone_start = end - int(words_per_chunk * 0.1)
            break_zone = words[break_zone_start:end]
            
            # Look for sentence endings
            for i, word in enumerate(reversed(break_zone)):
                if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                    end = end - i
                    break
        
        chunk_text = ' '.join(words[start:end])
        chunks.append(chunk_text)
        
        if end >= len(words):
            break
            
        start = end - overlap_words
    
    return chunks

def estimate_transcript_structure(text):
    """
    Try to infer meeting structure from content patterns
    No assumptions about keywords - just analyze the text
    """
    analysis = {
        'estimated_duration': 'Unknown',
        'speaker_changes': 0,
        'potential_speeches': 0,
        'question_segments': 0,
        'text_length': len(text),
        'word_count': len(text.split())
    }
    
    # Estimate duration based on word count (average speaking rate ~150 words/min)
    words = len(text.split())
    estimated_minutes = words / 150
    analysis['estimated_duration'] = f"~{estimated_minutes:.0f} minutes"
    
    # Look for potential speaker changes (long pauses in speech, topic shifts)
    sentences = re.split(r'[.!?]+', text)
    analysis['sentence_count'] = len(sentences)
    
    # Look for question patterns
    questions = len(re.findall(r'\?', text))
    analysis['question_segments'] = questions
    
    # Look for potential speech transitions
    transition_words = ['thank you', 'next speaker', 'now we', 'moving on', 'our next']
    transitions = sum(text.lower().count(phrase) for phrase in transition_words)
    analysis['potential_speeches'] = max(1, transitions)
    
    return analysis

# ============================================================================
# SUMMARIZATION ENGINE
# ============================================================================

def create_flexible_prompt(text, chunk_number=1, total_chunks=1, analysis=None):
    """
    Create a flexible prompt that doesn't assume specific meeting structure
    """
    chunk_info = f" (Part {chunk_number} of {total_chunks})" if total_chunks > 1 else ""
    
    analysis_info = ""
    if analysis:
        analysis_info = f"""
Context: This appears to be from a meeting transcript of approximately {analysis['estimated_duration']} 
with {analysis['word_count']} words total."""

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert at analyzing and summarizing meeting transcripts. You will receive raw transcript text from a Toastmasters meeting that was converted from audio using speech recognition. The text has no speaker labels, timestamps, or formatting.

Your task is to create a clear, structured summary that identifies the key content and activities that took place during the meeting.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Please analyze and summarize this meeting transcript{chunk_info}. Since this is raw speech-to-text output, there are no speaker labels or clear section markers.{analysis_info}

Please provide a structured summary with these sections:

**MEETING SUMMARY:**
- Overall meeting flow and structure
- Key activities that took place
- Approximate number of speakers/participants

**MAIN CONTENT AREAS:**
- Major topics or presentations discussed
- Key points and themes covered
- Any educational or developmental content

**NOTABLE DISCUSSIONS:**
- Significant conversations or exchanges
- Questions and answers
- Important decisions or announcements

**PARTICIPATION & ENGAGEMENT:**
- Evidence of member participation
- Interactive elements (if any)
- Overall meeting dynamics

**KEY TAKEAWAYS:**
- Main learning points
- Important information shared
- Action items or follow-ups mentioned

Raw transcript text:
{text}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    return prompt

def summarize_chunk(model, tokenizer, text, chunk_num=1, total_chunks=1, analysis=None):
    """Summarize a single chunk with flexible approach"""
    prompt = create_flexible_prompt(text, chunk_num, total_chunks, analysis)
    
    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=7000)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    # Generate summary
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=Config.MAX_SUMMARY_LENGTH,
            temperature=Config.TEMPERATURE,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.15,
            top_p=0.9
        )
    
    # Decode response
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the assistant's response
    if "<|start_header_id|>assistant<|end_header_id|>" in full_response:
        summary = full_response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()
    else:
        summary = full_response[len(prompt):].strip()
    
    return summary

def combine_chunk_summaries(summaries, analysis):
    """Combine multiple chunk summaries intelligently"""
    if len(summaries) == 1:
        return summaries[0]
    
    header = f"""# TOASTMASTERS MEETING SUMMARY

**Meeting Analysis:**
- Estimated Duration: {analysis['estimated_duration']}
- Total Words: {analysis['word_count']:,}
- Processed in: {len(summaries)} sections

---

"""
    
    # Combine summaries with clear section breaks
    combined_content = ""
    for i, summary in enumerate(summaries, 1):
        combined_content += f"\n## Section {i} Analysis:\n\n{summary}\n\n---\n"
    
    # Add a final synthesis section
    synthesis = f"""
## OVERALL MEETING SYNTHESIS:

This {analysis['estimated_duration']} meeting contained {analysis['word_count']:,} words of transcript content. The meeting appears to have involved {analysis.get('potential_speeches', 'multiple')} main segments with {analysis.get('question_segments', 0)} question/answer exchanges.

The above sections provide a comprehensive breakdown of the meeting content as it progressed chronologically.
"""
    
    return header + combined_content + synthesis

# ============================================================================
# FILE PROCESSING
# ============================================================================

def process_single_transcript(model, tokenizer, file_path):
    """Process a single raw transcript file"""
    print(f"\n📄 Processing: {os.path.basename(file_path)}")
    
    try:
        # Read file with encoding detection
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"   ✓ File read successfully with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise Exception("Could not read file with any encoding")
        
        # Basic validation
        if len(content.strip()) < 100:
            raise Exception("File appears to be too short (less than 100 characters)")
        
        # Clean the transcript
        cleaned_content = clean_whisper_transcript(content)
        print(f"   Original length: {len(content):,} characters")
        print(f"   Cleaned length: {len(cleaned_content):,} characters")
        
        # Analyze structure
        analysis = estimate_transcript_structure(cleaned_content)
        print(f"   Estimated duration: {analysis['estimated_duration']}")
        print(f"   Word count: {analysis['word_count']:,}")
        
        # Chunk the text
        chunks = smart_chunk_text(cleaned_content)
        print(f"   Split into {len(chunks)} chunks for processing")
        
        # Process each chunk
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"   Summarizing chunk {i}/{len(chunks)}... ", end="")
            try:
                summary = summarize_chunk(model, tokenizer, chunk, i, len(chunks), analysis)
                summaries.append(summary)
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
                summaries.append(f"Error processing chunk {i}: {str(e)}")
        
        # Combine all summaries
        final_summary = combine_chunk_summaries(summaries, analysis)
        
        # Save the result
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(Config.OUTPUT_FOLDER, f"{base_name}_summary.md")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_summary)
        
        print(f"   ✓ Summary saved to: {os.path.basename(output_path)}")
        return output_path, True, analysis
        
    except Exception as e:
        print(f"   ✗ Error processing {file_path}: {str(e)}")
        return None, False, None

def process_all_transcripts(model, tokenizer):
    """Process all transcript files"""
    print(f"\n🔍 Looking for transcript files in: {Config.INPUT_FOLDER}")
    
    # Find transcript files
    file_patterns = ['*.txt', '*.md', '*.text', '*.transcript']
    files = []
    
    if os.path.exists(Config.INPUT_FOLDER):
        for pattern in file_patterns:
            files.extend(glob.glob(os.path.join(Config.INPUT_FOLDER, pattern)))
    
    # Also check working directory for testing
    for pattern in file_patterns:
        files.extend(glob.glob(os.path.join("/kaggle/working", pattern)))
    
    if not files:
        print("❌ No transcript files found!")
        print("Expected file types: .txt, .md, .text, .transcript")
        print("Please upload your transcript files to the Kaggle dataset or working directory.")
        return []
    
    print(f"📁 Found {len(files)} files to process:")
    for f in files:
        print(f"   - {os.path.basename(f)}")
    
    # Process each file
    results = []
    successful = 0
    
    for file_path in files:
        output_path, success, analysis = process_single_transcript(model, tokenizer, file_path)
        results.append({
            'input_file': file_path,
            'output_file': output_path,
            'success': success,
            'analysis': analysis
        })
        if success:
            successful += 1
    
    # Summary report
    print(f"\n📊 PROCESSING COMPLETE!")
    print(f"   ✓ Successfully processed: {successful}/{len(files)} files")
    if successful > 0:
        print(f"   📁 Summaries saved to: {Config.OUTPUT_FOLDER}")
    
    return results

# ============================================================================
# MAIN EXECUTION & TESTING
# ============================================================================

def create_sample_transcript():
    """Create a realistic sample transcript for testing"""
    sample = """
    Welcome everyone to our meeting today. I hope everyone is doing well. Let's get started with our agenda for this evening.

    So first we have our opening remarks and then we'll move into our main presentations. We have several members who will be sharing with us today.

    I'd like to start by introducing our first presenter who will be talking about effective communication techniques. This is an important topic for all of us to learn about and improve our skills in this area.

    Thank you for that introduction. Today I want to talk about the power of storytelling in public speaking. When we tell stories we connect with our audience on an emotional level. Stories help us remember information better than just facts and figures alone.

    I remember when I first started speaking publicly I was terrified. My hands would shake and my voice would tremble. But over time I learned that preparation and practice are key to building confidence.

    That's excellent advice about preparation. Now let's move on to our next segment where we'll hear from another member about leadership development.

    Leadership is something we all need to work on regardless of our current position. Whether you're leading a team at work or volunteering in your community these skills are valuable.

    I think one of the most important aspects of leadership is listening. We need to really hear what people are saying not just wait for our turn to talk. Active listening builds trust and helps us make better decisions.

    Those are great points about listening skills. Now we have time for some interactive discussion. I'd like to ask everyone to think about a time when good communication made a difference in your life.

    I can share an example from my workplace. We had a project that was falling behind schedule and there was tension between departments. By having an open conversation where everyone could express their concerns we found solutions that worked for everyone.

    That's a perfect example of collaborative problem solving. Communication really is at the heart of effective teamwork.

    Does anyone else have an experience they'd like to share about communication or leadership?

    I have one from my volunteer work. We were organizing a fundraising event and initially people had very different ideas about how to proceed. By taking time to listen to all perspectives we created a plan that incorporated the best elements from everyone's suggestions.

    These examples show how important it is to create an environment where people feel comfortable sharing their ideas. Psychological safety is crucial for good communication.

    As we wrap up today I want to thank everyone for their participation and insights. Remember that developing these skills takes practice and patience with yourself.

    Our next meeting will be next week at the same time. Please think about topics you'd like to explore in future sessions.

    Thank you everyone for a productive discussion today. Have a great rest of your week.
    """
    
    return sample

def test_with_sample():
    """Test the system with a sample transcript"""
    print("\n🧪 TESTING WITH SAMPLE TRANSCRIPT")
    print("=" * 50)
    
    # Create sample file
    sample_path = "/kaggle/working/sample_meeting.txt"
    with open(sample_path, 'w') as f:
        f.write(create_sample_transcript())
    
    print("✓ Sample transcript created")
    
    # Process the sample
    model, tokenizer = load_model()
    process_single_transcript(model, tokenizer, sample_path)
    
    print("✓ Sample processing completed!")

def main():
    """Main execution function"""
    print("🎤 TOASTMASTERS TRANSCRIPT SUMMARIZER")
    print("=" * 60)
    print("📝 Designed for raw Whisper speech-to-text output")
    print("🔧 No speaker labels or timestamps required")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Load model
    try:
        model, tokenizer = load_model()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("💡 Make sure you have GPU enabled and sufficient memory")
        return
    
    # Process all files
    results = process_all_transcripts(model, tokenizer)
    
    # Display final results
    if results:
        print("\n📋 FINAL RESULTS:")
        print("-" * 40)
        for result in results:
            if result['success']:
                print(f"✓ {os.path.basename(result['input_file'])}")
                if result['analysis']:
                    print(f"   Duration: {result['analysis']['estimated_duration']}")
                    print(f"   Words: {result['analysis']['word_count']:,}")
                print(f"   → {os.path.basename(result['output_file'])}")
            else:
                print(f"✗ {os.path.basename(result['input_file'])} - FAILED")
    else:
        print("\n💡 No files were processed. Try running test_with_sample() first.")
    
    print(f"\n🎯 Processing complete! Check {Config.OUTPUT_FOLDER} for your summaries.")

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Uncomment to test with sample data first:
    # test_with_sample()
    
    # Run main program
    main()