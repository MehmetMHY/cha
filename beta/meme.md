1. Basic Invocation (no arguments or a direct question):
   • cha
   • cha "<some question or request>"
   Example:
   cha "in type script how can I check if .canvas.edges is an empty array?"

2. Code-Dump/Debug Flags:
   • cha --code_dump
   • cha -d

3. Answer Search:
   • cha -a
   • cha -a "<question>"
   Example:
   cha -a "what is the goal of life"

4. File Input with -f:
   • cha -f <FILE>
   Example:
   cha -f index.js

5. Model Selection with -m:
   • cha -m <MODEL_NAME>
   Example:
   cha -m "o3-mini"

6. OCR (Extract Text from Files):
   • cha -ocr <FILE> [> <OUTPUT_FILE>]
   Examples:
   cha -ocr ./README.md
   cha -ocr meme.jpg > output.txt

7. Platform Switching (-p) and Model Combined:
   • cha -p "<PLATFORM_OR_URL|API_KEY_ENV>" -m "<MODEL_NAME>"
   Examples:
   cha -p "https://api.deepseek.com|DEEP_SEEK_API_KEY" -m "deepseek-chat"
   cha -p "llama3-70b-8192|GROQ_API_KEY" -m "llama3-70b-8192"

8. Platform Switching with just "-p" for a dynamic platform switching:
   • cha -p

9. Model Autoselection (-sm):
   • cha -sm
   • cha -sm <MODEL_NAME>

10. Token Counting (-t) with a File:
    • cha -t -f <FILE>
    Example:
    cha -t -f README.md

11. Direct “How to” / “Make me” / “Craft me” Questions:
    These appear frequently with “cha” followed by a question/request
    referencing programming, shell commands, or general tasks, for example:
    • cha how many seconds is in a day
    • cha in python how can I save a dict to a json
    • cha craft me a unix command to find all Cargo.toml
    • cha make me a simple flask API
    … and many more along similar lines.

In essence, your unique “cha” CLI usage falls into these main patterns:
• Running “cha” with a direct query.  
• Doing code dumps or debug dumps (-code_dump, -c, -d).  
• Performing answer searches (-a).  
• Feeding in file input (-f).  
• Specifying or switching models (-m, -sm).  
• Running OCR operations (-ocr).  
• Switching platforms (-p).  
• Checking token counts (-t).  
• Asking a broad variety of how-to / make-me requests directly after “cha …”.
