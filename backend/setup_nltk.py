"""
NLTK Setup Script
Downloads required NLTK resources for the first time
"""

import nltk
import ssl

def setup_nltk():
    """Download required NLTK resources"""
    try:
        # Create unverified SSL context for NLTK downloads
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        # List of required NLTK resources
        resources = [
            'punkt',
            'stopwords',
            'wordnet',
            'averaged_perceptron_tagger',
            'maxent_ne_chunker',
            'words',
            'omw-1.4'  # Open Multilingual Wordnet
        ]
        
        print("Downloading NLTK resources...")
        
        for resource in resources:
            try:
                print(f"Downloading {resource}...")
                nltk.download(resource, quiet=True)
                print(f"✓ {resource} downloaded successfully")
            except Exception as e:
                print(f"✗ Error downloading {resource}: {e}")
        
        print("\nNLTK setup completed!")
        
    except Exception as e:
        print(f"Error during NLTK setup: {e}")

if __name__ == "__main__":
    setup_nltk()
