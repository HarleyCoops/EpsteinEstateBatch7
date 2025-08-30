import os
import google.generativeai as genai
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Analyze cultural shifts in translated German letters.')
parser.add_argument('--output-base', type=str, help='Base directory containing the english_output folder and where analysis_output will be created')
parser.add_argument('--input-file', type=str, help='Path to combined English translation file (default: english_output/combined_english_translation.txt)')
parser.add_argument('--output-dir', type=str, help='Output directory for analysis results (default: analysis_output)')
args = parser.parse_args()

# Determine paths based on arguments
if args.output_base:
    # When using --output-base, look for input in that folder's english_output
    base_input_file = os.path.join(args.output_base, "english_output", "combined_english_translation.txt")
    base_output_dir = os.path.join(args.output_base, "analysis_output")
else:
    # Default paths
    base_input_file = "english_output/combined_english_translation.txt"
    base_output_dir = "analysis_output"

# Configuration
CONFIG = {
    "input_file": args.input_file if args.input_file else base_input_file,
    "output_dir": args.output_dir if args.output_dir else base_output_dir,
    "gemini_model": "gemini-1.5-flash",
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

class CulturalShiftsAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer with Gemini model."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(CONFIG["gemini_model"])
        
        # Create output directory if it doesn't exist
        os.makedirs(CONFIG["output_dir"], exist_ok=True)

    def load_text(self, file_path: str) -> str:
        """Load and return the content of the text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")

    def generate_prompts(self, text: str) -> Dict[str, str]:
        """Generate analysis prompts for Gemini."""
        base_prompt = """
        You are a cultural historian analyzing personal correspondence from post-WWII Germany. 
        The following text contains letters written by Dorle, a young German woman in the mid-20th century.
        Analyze the text with a focus on cultural shifts and international influences.
        
        Text to analyze:
        """
        
        return {
            "window_to_west": f"""{base_prompt}
            [FOCUS ON AMERIKAHAUS]
            
            Analyze the cultural significance of Dorle's visit to the Amerikahaus. Consider:
            1. The symbolic meaning of the Amerikahaus in post-war Germany
            2. The nature of the English discussions held there
            3. How this reflects changing attitudes towards American culture
            4. The role of language learning in cultural exchange
            
            Provide specific examples from the text and historical context.
            
            Text:
            {text}
            """,
            
            "beyond_borders": f"""{base_prompt}
            [FOCUS ON INTERNATIONAL AMBITIONS]
            
            Analyze Dorle's international aspirations and connections. Consider:
            1. References to England, France, Switzerland, and Canada
            2. The significance of these specific countries in post-war Europe
            3. How these aspirations reflect broader generational shifts
            4. The contrast between local and international perspectives
            
            Provide specific examples from the text and historical context.
            
            Text:
            {text}
            """
        }

    def analyze_with_gemini(self, prompt: str) -> str:
        """Send prompt to Gemini and return the response."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": CONFIG["temperature"],
                    "top_p": CONFIG["top_p"],
                    "top_k": CONFIG["top_k"],
                    "max_output_tokens": CONFIG["max_output_tokens"],
                }
            )
            return response.text
        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")

    def save_analysis(self, analysis: Dict[str, str]) -> str:
        """Save the analysis to a timestamped Markdown file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(CONFIG["output_dir"]) / f"cultural_analysis_{timestamp}.md"
        
        # Create markdown content
        md_content = "# Cultural Shifts Analysis\n\n"
        md_content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Add each analysis section
        for topic, content in analysis.items():
            # Convert snake_case to Title Case for headings
            heading = topic.replace('_', ' ').title()
            md_content += f"\n## {heading}\n\n{content}\n"
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return str(output_path)

    def run_analysis(self):
        """Run the complete cultural shifts analysis."""
        print("Starting cultural shifts analysis...")
        
        try:
            # Load the text
            text = self.load_text(CONFIG["input_file"])
            print(f"Loaded {len(text)} characters from {CONFIG['input_file']}")
            
            # Generate and run prompts
            prompts = self.generate_prompts(text)
            results = {}
            
            for topic, prompt in prompts.items():
                print(f"\nAnalyzing: {topic.replace('_', ' ').title()}...")
                results[topic] = self.analyze_with_gemini(prompt)
                print(f"✓ Completed analysis for {topic}")
            
            # Save results
            output_file = self.save_analysis(results)
            print(f"\nAnalysis complete! Results saved to: {output_file}")
            
            return results
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            raise

def main():
    # Initialize analyzer
    try:
        analyzer = CulturalShiftsAnalyzer()
        
        # Run analysis
        results = analyzer.run_analysis()
        
        # Print summary
        print("\n" + "="*50)
        print("CULTURAL SHIFTS ANALYSIS SUMMARY")
        print("="*50)
        
        for topic, analysis in results.items():
            print(f"\n{'-'*50}")
            print(f"{topic.replace('_', ' ').upper()}")
            print(f"{'-'*50}")
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please ensure you have set the GOOGLE_API_KEY environment variable.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
