#!/bin/sh
#модули, необходимые большинству людей
./bqt2mod.py --cv /home/cepreu/.wine/drive_c/BibleQuote/RstStrong/BIBLEQT.INI
./bqt2mod.py --moduletype Dictionary --dictionarytype GreekStrong /home/cepreu/.wine/drive_c/BibleQuote/Strongs/GREEK.HTM
./bqt2mod.py --moduletype Dictionary --dictionarytype HebrewStrong /home/cepreu/.wine/drive_c/BibleQuote/Strongs/HEBREW.HTM
./bqt2mod.py --moduletype Dictionary --linebreaktag br /home/cepreu/.wine/drive_c/BibleQuote/Dictionaries/zondervan.htm
./bqt2mod.py --notetag i --titletag h3 --cv /home/cepreu/.wine/drive_c/BibleQuote/MDR/BibleQT.ini
./bqt2mod.py --cv /home/cepreu/.wine/drive_c/BibleQuote/Kuznetsova/BIBLEQT.INI
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/Commentaries/NGSB/BIBLEQT.INI
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/Christian30-1000/BIBLEQT.INI
./bqt2mod.py --moduletype Apocrypha /home/cepreu/.wine/drive_c/BibleQuote/RstStrong/BIBLEQT.INI
./bqt2mod.py --cv /home/cepreu/.wine/drive_c/BibleQuote/NT_Cassian/Bibleqt.ini
./bqt2mod.py --cv /home/cepreu/.wine/drive_c/BibleQuote/NT_SlovoLife/Bibleqt.ini
./bqt2mod.py --cv /home/cepreu/.wine/drive_c/BibleQuote/RBSOT/BIBLEQT.INI
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/halley/bibleqt.ini
./bqt2mod.py --notetag font --cv /home/cepreu/.wine/drive_c/BibleQuote/Lutkovsky/BIBLEQT.INI
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/DNTC/bibleqt.ini
./bqt2mod.py --moduletype Book --encoding utf_8 --encodingbooks utf_8 /home/cepreu/.wine/drive_c/BibleQuote/BibleAtlasRus/bibleqt.ini
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/bibledict/bibleqt.ini
./bqt2mod.py --moduletype Commentary --cv /home/cepreu/.wine/drive_c/BibleQuote/Commentaries/Kuznetsova-Comments/BIBLEQT.INI
./bqt2mod.py --encoding utf_8 --encodingbooks utf_8 /home/cepreu/.wine/drive_c/BibleQuote/Bib_Ru_CJB/bibleqt.ini
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/Commentaries/Keyle/BIBLEQT.INI
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/Commentaries/McDonald/bibleqt.ini
./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/Commentaries/Lop/bibleqt.ini
./bqt2mod.py --tt b --l=en /home/cepreu/.wine/drive_c/BibleQuote/NASB/BIBLEQT.INI
./bqt2mod.py --moduletype Dictionary --linebreaktag br /home/cepreu/.wine/drive_c/BibleQuote/Dictionaries/vikhlyantsev.htm
./bqt2mod.py --l=en /home/cepreu/.wine/drive_c/BibleQuote/Bible_NIV/BIBLEQT.INI

#модули, полезные в качестве дополнительного тестового комплекта
#./bqt2mod.py --encoding utf_8 --encodingbooks utf_8 /home/cepreu/.wine/drive_c/BibleQuote/BHS+/bibleqt.ini
#./bqt2mod.py --encoding utf_8 --encodingbooks utf_8 --language en /home/cepreu/.wine/drive_c/BibleQuote/IHOT+/bibleqt.ini
#./bqt2mod.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote/Bible_Gravur_Dore/bibleqt.ini

