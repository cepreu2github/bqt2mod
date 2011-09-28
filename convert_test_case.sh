#!/bin/sh
#модули, необходимые большинству людей
./new.py --cv /home/cepreu/.wine/drive_c/BibleQuote6/RstStrong/BIBLEQT.INI
./new.py --moduletype Dictionary --dictionarytype GreekStrong /home/cepreu/.wine/drive_c/BibleQuote6/Strongs/GREEK.HTM
./new.py --moduletype Dictionary --dictionarytype HebrewStrong /home/cepreu/.wine/drive_c/BibleQuote6/Strongs/HEBREW.HTM
./new.py --moduletype Dictionary --linebreaktag br /home/cepreu/.wine/drive_c/BibleQuote6/Dictionaries/zondervan.htm
./new.py --notetag i --titletag h3 --cv /home/cepreu/.wine/drive_c/BibleQuote6/MDR/BibleQT.ini
./new.py --cv /home/cepreu/.wine/drive_c/BibleQuote6/Kuznetsova/BIBLEQT.INI
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/Commentaries/NGSB/BIBLEQT.INI
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/Christian30-1000/BIBLEQT.INI
./new.py --moduletype Apocrypha /home/cepreu/.wine/drive_c/BibleQuote6/RstStrong/BIBLEQT.INI
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/Bible_Gravur_Dore/bibleqt.ini
./new.py --cv /home/cepreu/.wine/drive_c/BibleQuote6/NT_Cassian/Bibleqt.ini
./new.py --cv /home/cepreu/.wine/drive_c/BibleQuote6/NT_SlovoLife/Bibleqt.ini
./new.py --cv /home/cepreu/.wine/drive_c/BibleQuote6/RBSOT/BIBLEQT.INI
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/halley/bibleqt.ini
./new.py --notetag font --cv /home/cepreu/.wine/drive_c/BibleQuote6/Lutkovsky/BIBLEQT.INI
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/DNTC/bibleqt.ini
./new.py --moduletype Book --encoding utf_8 --encodingbooks utf_8 /home/cepreu/.wine/drive_c/BibleQuote6/BibleAtlasRus/bibleqt.ini
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/bibledict/bibleqt.ini
./new.py --moduletype Commentary --cv /home/cepreu/.wine/drive_c/BibleQuote6/Commentaries/Kuznetsova-Comments/BIBLEQT.INI
./new.py --encoding utf_8 --encodingbooks utf_8 /home/cepreu/.wine/drive_c/BibleQuote6/Bib_Ru_CJB/bibleqt.ini
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/Commentaries/Keyle/BIBLEQT.INI
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/Commentaries/McDonald/bibleqt.ini
./new.py --moduletype Book /home/cepreu/.wine/drive_c/BibleQuote6/Commentaries/Lop/bibleqt.ini

#модули, полезные в качестве дополнительного тестового комплекта
#./new.py --encoding utf_8 --encodingbooks utf_8 /home/cepreu/.wine/drive_c/BibleQuote6/BHS+/bibleqt.ini
#./new.py --encoding utf_8 --encodingbooks utf_8 --language en /home/cepreu/.wine/drive_c/BibleQuote6/IHOT+/bibleqt.ini
