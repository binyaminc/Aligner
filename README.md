# Aligner
 
## Objective
Aligning and centering scanned documents
## How to use
1. Clone the repo (`git clone https://github.com/binyaminc/Aligner.git`)
2. Run the file `book_aligner.py`, with an argument of the book path
3. The aligned book will be created near the given book (together with a diractory consists of the seperated and aligned pages)
## Example of single page
The scanned page before and after the aligning:

![aligning_page](https://user-images.githubusercontent.com/71450794/172434409-243f9db2-8861-44c3-8e68-109c2639161d.png)

**_NOTES:_** The program is designed specifically to scanned documents, which means:
1. Angle of text bigger than 10 degrees is considered a mistake in recognition (scanned documents aren't that rotated, e.g. the above example has only 1.8 degrees)
2. The process is text-based (using pytesseract OCR), therefore it won't work optimally with pictures 
