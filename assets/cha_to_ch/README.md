# convert_cha_to_ch

## About

Converts chat history files from the **[Cha](https://github.com/MehmetMHY/cha)** format (`cha_hs_*.json`) to the newer **[Ch](https://github.com/MehmetMHY/ch)** session format (`ch_session_*.json`). As of **August 23, 2025**, Cha has been replaced by Ch, but the history file structure changed between the two projects. This script handles all the differences.

## Usage

```bash
# convert all files using defaults (./cha_chats -> ./ch_chats)
python3 convert_cha_to_ch.py

# specify input and output
python3 convert_cha_to_ch.py -i /path/to/cha_chats -o /path/to/ch_chats

# convert a single file
python3 convert_cha_to_ch.py -i session.json -o ./out/

# preview without writing anything
python3 convert_cha_to_ch.py --dry-run

# verbose output
python3 convert_cha_to_ch.py -v

# check collisions against a custom Ch sessions directory
python3 convert_cha_to_ch.py -c /path/to/ch/sessions
```

## Options

```bash
-c, --check-dir   Dir of existing Ch sessions to check for collisions (default: ~/.ch/tmp)
-i, --input       Input file or directory (default: ./cha_chats relative to script)
-o, --output      Output directory (default: ./ch_chats relative to script)
--in-prefix       Filename prefix to match (default: cha_hs_)
--out-prefix      Filename prefix for output (default: ch_session_)
--indent          JSON indentation level (default: 2)
--dry-run         Show what would be converted without writing files
-v, --verbose     Show per-file conversion details
-q, --quiet       Only show the summary line
```
