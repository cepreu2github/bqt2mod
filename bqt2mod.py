#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C)  2011 Варюхин Сергей <cepreu.mail@gmail.com>,
# Александр Сапронов http://warmonger72.blogspot.com/
#This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

################################################################################
# Конвертер модулей из формата программы "Цитата из библии" в формат проекта
# Sword.   
#
# Программа создает в выходной папке структуру папок и файлов, соответствующую
# структуре, согласно которой хранятся модули в программах на базе библиотеки
# Sword. То есть достаточно просто скопировать содержимое выходной папки в
# папку для хранения модулей, например "~/.sword" (для Linux) или в папку
# "C:\Program Files\CrossWire\The SWORD Project" (для Windows), и получить
# сконвертированный модуль установленным в системе.
# Для нормальной работы программе необходимо наличие в системе утилит от проекта
# Sword: osis2mod, tei2mod, xml2gbs или по пути, прописанному в PATH или в папке
# с программой. Для Windows их можно скачать отдельно по адресу:
# http://crosswire.org/ftpmirror/pub/sword/utils/win32/ (выбирайте последнюю
# версию архива sword-utilities (например в данный момент это
# sword-utilities-1.6.2.zip).
# Если у вас Linux, то эти утилиты поставляются в составе пакета, содержащего
# библиотеку sword. В разных дистрибутивах называется по-разному, например
# libsword8 (в Ubuntu, установка apt-get install libsword8), sword (в Fedora, 
# установка yum install sword).
#
################################################################################
import string, sys, os, codecs, re, subprocess, datetime, shutil
from HTMLParser import HTMLParser, HTMLParseError

ScriptVersion = '0.8.5'

class ConvertError(Exception):
	pass

class Charsets:
	Symbol = [
	['A','Α'], ['B','Β'], ['G','Γ'], ['D','Δ'], ['E','Ε'], ['Z','Ζ'], ['H','Η'],
	['Q','Θ'], ['I','Ι'], ['K','Κ'], ['L','Λ'], ['M','Μ'], ['N','Ν'], ['X','Ξ'],
	['O','Ο'], ['P','Π'], ['R','Ρ'], ['S','Σ'], ['T','Τ'], ['U','Υ'], ['F','Φ'],
	['C','Χ'], ['Y','Ψ'], ['W','Ω'], ['a','α'], ['b','β'], ['g','γ'], ['d','δ'],
	['e','ε'], ['z','ζ'], ['h','η'], ['q','θ'], ['i','ι'], ['k','κ'], ['l','λ'],
	['m','μ'], ['n','ν'], ['x','ξ'], ['o','ο'], ['p','π'], ['r','ρ'], ['V','ς'],
	['s','σ'], ['t','τ'], ['u','υ'], ['f','φ'], ['c','χ'], ['y','ψ'], ['w','ω'],
	['J','ϑ'], ['j','ϕ'], ['v','ς'], ['"','᾽'], ['#','῎'], ['$','῎'], ['%','῞'],
	["'",'᾽'], ['+','΅'], ['/','΄'], [':','῾'],	[';','῾'], ['\\','`'],['^','῞'],
	['`','ͺ']
	]
	BQTGrk = Symbol
	BQTHeb = [
	['"','‍ַ'], ['#','ֲ'], ['$','‍ֳ'], ['%','ֱ'], ["'",'‍ַ'], ['+','ּ'], ['/','ָ'],
	[';','ְ'], ['=','ּ'], ['C','ֻ'], ['F','ֹ‍ׂ'], ['I','ִ'], ['K','ך'], ['M','ם'],
	['N','ן'], ['P','ף'], ['S','‍ׂ'], ['U','ץ'], ['V','ׁ'], ['[','ֵ'], ['\\','‍ׇ'],
	[']','ֶ'], ['_','ְ'], ['a','א'], ['b','ב'], ['c','ֻ'], ['d','ד'], ['e','ע'],
	['f','‍ֹ'], ['g','נ'], ['h','ה'], ['i','‍ׅ'], ['j','ט'], ['k','כ'], ['l','ל'],
	['m','מ'], ['n','נ'], ['o','ס'], ['p','פ'], ['q','ק'], ['r','ר'], ['s','ש'],
	['t','ת'], ['u','צ'], ['v','ש'], ['w','ו'], ['x','ח'], ['y','י'], ['z','ז'],
	['{','ֵ'], ['}','ֶ']
	]

# класс, реализующий основную функциональность
class CConverter:

	class CHTMLParser(HTMLParser):
		HebrewFonts = [Charsets.BQTHeb]
		Result = ''
		def __init__(self, Converter):
			self.DefaultCharset = Converter.DefaultCharset
			self.CurrentCharset = [self.DefaultCharset]
			self.Converter = Converter
		
		def handle_starttag(self, tag, attrs):
			#если используется нестандартный шрифт, текст необходимо
			#перекодировать, чтобы он выглядел сохранить в utf-представлении
			#символы этого шрифта
			if tag == 'font':
				for Pair in attrs:
					if Pair[0] == 'face':
						#ищем соответсвующий charset
						if hasattr(Charsets, Pair[1]):
							self.CurrentCharset.append(getattr(Charsets,\
								Pair[1]))
						else:
							self.CurrentCharset.append(None)
					else:
						self.CurrentCharset.append(self.CurrentCharset[-1])
			#некоторые теги, не описанные в стандарте, но часто используемые
			#авторами модулей
			if tag == self.Converter.Options.NoteTag:
				self.Result += '<i>'
			if tag == self.Converter.Options.TitleTag:
				self.Result += '<b>'
			if tag == self.Converter.Options.LineBreakTag:
				self.Result += '<p> </p>'
			#обработка изображений
			if tag == 'img':
				ImagePath = [q[1] for q in attrs if q[0]=='src'][0]
				#вставка в результат соответствующего тега
				if not self.Converter.Options.ModuleType == 'Dictionary':
					self.Result+='<figure src="'+ImagePath+'"/>'
				else:
					self.Result+='<figure> <graphic url="'+\
						ImagePath+'"/> </figure>'
				#сохранение информации об изображении для последующих стадий
				self.Converter.ImagesList.append(ImagePath)
			self.Result+=' '
	
		def handle_startendtag(tag, attrs):
			self.Result+=' '
	
		def handle_endtag(self, tag):
			#возвращение к предыдущему шрифту
			if tag == 'font':
				self.CurrentCharset.pop()
				if len(self.CurrentCharset) == 0:
					self.CurrentCharset = [self.DefaultCharset]
			#закрытие нестандартных тегов
			if tag == self.Converter.Options.NoteTag:
				self.Result += '</i>'
			if tag == self.Converter.Options.TitleTag:
				self.Result += '</b>'
			self.Result+=' '
	
		#обработка основного текста модуля	
		def handle_data(self, data):
			if self.CurrentCharset[-1]!=None:
				self.Result+=self.RecodeToCharset(data, self.CurrentCharset[-1])
			else:
				self.Result+=data
	
		#перевод текста к нужному набору символов
		def RecodeToCharset(self, Text, Charset):
			NewText = ''
			#если испльзуется еврейский шрифт, еще надо поменять порядок
			#символов в строке, потому-чо в utf-8 иврит пишется справа налево
			if Charset in self.HebrewFonts:
				Text = Text[::-1]
			for i in xrange(0, len(Text)):
				Found = False
				for Pair in Charset:
					if Pair[0]==Text[i]:
						NewText = NewText + Pair[1]
						Found = True
				if not Found:
					NewText = NewText + Text[i]
			if Charset in self.HebrewFonts:
				NewText = '<p>'+NewText+'</p>'
			return NewText

	#пояснение: 1 - стронги на иврите, 2- стронги греческие, 3 -другое
	TableBooks = [
	['Genesis',     	'Gen', 		1], #от сюда иврит
	['Exodus',      	'Exod', 	1],	['Leviticus',   	'Lev', 		1],
	['Numbers',     	'Num', 		1],	['Deuteronomy', 	'Deut', 	1],
	['Joshua',      	'Josh', 	1],	['Judges',      	'Judg', 	1],
	['Ruth',        	'Ruth', 	1],	['1Samuel',     	'1Sam', 	1], 
	['2Samuel',     	'2Sam', 	1],	['1Kings',      	'1Kgs', 	1],
	['2Kings',      	'2Kgs', 	1],	['1Chron',      	'1Chr', 	1],   
	['2Chron',			'2Chr', 	1],	['Ezra',       		'Ezra', 	1],
	['Nehemiah',    	'Neh',		1],	['Esther',     		'Esth', 	1],   
	['Job',         	'Job', 		1],	['Psalm',      		'Ps', 		1],
	['Proverbs',    	'Prov', 	1],	['Ecclesia',    	'Eccl', 	1],   
	['Song',        	'Song', 	1],	['Isaiah',      	'Isa', 		1],
	['Jeremiah',   	 	'Jer', 		1],	['Lament',      	'Lam', 		1],    
	['Ezekiel',     	'Ezek',		1],	['Daniel',      	'Dan', 		1],
	['Hosea',      	 	'Hos', 		1],	['Joel',        	'Joel', 	1],   
	['Amos',       	 	'Amos', 	1],	['Obadiah',     	'Obad', 	1],
	['Jonah',      		'Jonah', 	1],	['Micah',       	'Mic', 		1],    
	['Nahum',       	'Nah', 		1],	['Habakkuk',    	'Hab', 		1],
	['Zephaniah',   	'Zeph', 	1],	['Haggai',      	'Hag', 		1],
	['Zechariah',   	'Zech', 	1],
	['Malachi',     	'Mal', 		1], #до сюда
	['Matthew',    	 	'Matt', 	2], # от сюда греческие
	['Mark',        	'Mark', 	2],	['Luke',       		'Luke', 	2],
	[' John',        	'John', 	2],	['Acts',        	'Acts', 	2],
	['James',       	'Jas', 		2],	['1Peter',      	'1Pet', 	2],
	['2Peter',      	'2Pet', 	2],	['1John',           '1John', 	2], 
	['2John',       	'2John', 	2],	['3John',       	'3John', 	2],
	['Jude',        	'Jude', 	2],	['Romans',      	'Rom', 		2], 
	['1Corinthians',	'1Cor', 	2],	['2Corinthians',	'2Cor', 	2],
	['Galatians',   	'Gal', 		2],	['Ephesian',    	'Eph', 		2],   
	['Philippians', 	'Phil', 	2],	['Colossians',      'Col', 		2],
	['1Thessalonians',  '1Thess', 	2],	['2Thessalonians',  '2Thess', 	2], 
	['1Timothy',    	'1Tim', 	2],	['2Timothy',      	'2Tim', 	2],
	['Titus',      		'Titus', 	2],	['Philemon',       	'Phlm', 	2],   
	['Hebrews',     	'Heb', 		2],
	['Revelation',  	'Rev', 		2], #до сюда
	['1Мак',            '1Mac', 	3],	['2Мак',       		'2Mac', 	3],
	['3Мак',          	'3Mac', 	3],	['Варух',         	'Bar', 		3], 
	['2Ездр',       	'2Esd', 	3],	['3Ездр',          	'3Esd', 	3],
	['Иудиф',       	'Judith', 	3],	['Посл.Иер.',   	'EpJer', 	3],
	['Прем.Сол.',      	'WSo', 		3],	['Сир',         	'Sir', 		3],
	['Тов.',           	'Tob', 		3],	['Прим.',       	'Prim', 	3],
	]
	
	JustBooks = ['Book', 'Apocrypha']
	
	class CCurrentBookSettings:
		pass
	ImagesList = []
	
	def __init__(self, Options):
		self.Options=Options
		self.CurrentBookSettings = self.CCurrentBookSettings()
		self.DefaultCharset=None
		if self.Options.CharsetName!='':
			if hasattr(Charsets, self.Options.CharsetName):
				self.DefaultCharset=getattr(Charsets, self.Options.CharsetName)
		#создание HTML-парсера и OSIS-райтера
		self.HTMLParser = self.CHTMLParser(self)
		self.OsisWriter = self.COsisWriter(self)
		#делаем пути абсолютными, чтобы избежать потенциальных проблем
		self.Options.InputFileName = os.path.abspath(self.Options.InputFileName)
		self.Options.OutputPath = os.path.abspath(self.Options.OutputPath)
		#определяем рабочие пути
		self.BQModuleDirectory = os.path.dirname(self.Options.InputFileName)+'/'
		self.OutputDirectory = ''.join(self.Options.OutputPath)+'/'
		self.ConfFileDirectory = self.OutputDirectory+'mods.d/'
		if self.Options.ModuleType == 'Bible':
			self.DataPath = 'modules/texts/ztext/'
		elif self.Options.ModuleType == 'Commentary':
			self.DataPath = 'modules/comments/zcom/'
		elif self.Options.ModuleType in self.JustBooks:
			self.DataPath = 'modules/genbook/rawgenbook/'
		#создаем рабочие папки в случае их отсутствия
		if not os.path.exists(self.OutputDirectory): 
			os.makedirs(self.OutputDirectory) 
		if not os.path.exists(self.ConfFileDirectory):
			os.makedirs(self.ConfFileDirectory)
	
	#копирование изображения в папку с модулем
	def CopyImages(self, TextPath):
		for ImagePath in self.ImagesList:
			DestinationPath = TextPath+ImagePath
			if not os.path.exists(os.path.dirname(DestinationPath)): 
				os.makedirs(os.path.dirname(DestinationPath)) 
			shutil.copyfile(self.GetFileNameInProperCase(\
				self.BQModuleDirectory+ImagePath),\
				DestinationPath)

	#функция удаления разнообразного мусора из текста
	def RemoveGarbage(self, Text):
		#убираем переводы строки
		Text = Text.replace('\r',' ')
		Text = Text.replace('\n',' ')
		#переводим текст в правильный набор символов
		Text = self.StripTagsAndRecode(Text)
		#удаление лишних пробелов
		Text = Text.lstrip()
		Text = self.RemoveDoubleSpaces(Text)
		return Text

	#запись записи в выходной файл
	def FinalizeEntry(self, KeyWord, CurrentEntry):
		CurrentEntry = CurrentEntry.decode(self.Options.ModuleEncoding).\
			encode('utf_8')
		#закрывающий тег h4 в итоге отделяет ключевое слово
		#от его объяснения
		if KeyWord == '':
			KeyWord = CurrentEntry.split('</h4>',1)[0]
		if '</h4>' in CurrentEntry:
			Explanation = CurrentEntry.split('</h4>',1)[1]
		else:
			Explanation = CurrentEntry
		#удаление лишних тегов, пробелов и прочей ерунды
		KeyWord = self.RemoveGarbage(KeyWord)
		Explanation = self.RemoveGarbage(Explanation)
		#запись результата в xml
		self.TEIFile.write('\t\t<entryFree n="'+KeyWord+'">\n')
		self.TEIFile.write('\t\t\t<title>'+KeyWord+'</title>\n')
		self.TEIFile.write('\t\t\t<def>'+Explanation+'</def>\n')
		self.TEIFile.write('\t\t</entryFree>\n')
	
	#основная функция для конвертирования словарей
	def MakeConversionToTEI(self):
		#создание TEI-файла
		self.DictionaryName = os.path.basename(self.Options.InputFileName).\
			upper().rstrip('.HTM')
		self.CheckModuleName(self.DictionaryName)
		self.TEIFileName = self.OutputDirectory+self.DictionaryName+'.xml'
		self.TEIFile = file(self.TEIFileName, 'w')
		self.ConfFile = file(self.ConfFileDirectory+self.DictionaryName+\
			'.conf', 'w')
		#запись заголовка
		self.WriteTEIHeader()
		#собственно преобразование
		self.InputFile = file(self.Options.InputFileName, 'r')
		self.IdxFile = file(self.GetFileNameInProperCase(self.Options.\
			InputFileName.rpartition('.')[0]+'.idx'), 'r')
		#в оригинальной BibleQuote версии 5.0 просто словари и словари Стронга
		#обрабатываются по-разному. В греческом словаре Стронга, который идет
		#в поставке программы, содержатся ошибки в исчислении смещений в файле
		#.idx, которые не позволяют применить один код ко всем типам словарей
		if self.Options.DictionaryType in ['GreekStrong','HebrewStrong']:
			CurrentEntry = ''
			WritingEntry = False
			for Line in self.InputFile:
				#получаем список записей
				Entries = Line.split('<h4>')
				#первый блок записываем в конец текущей записи
				if len(Entries) > 0 and WritingEntry:
					CurrentEntry+=Entries[0]
					Entries = Entries[1:]
				elif not WritingEntry:
					Entries = Entries[1:]
				#остальные блоки записываем последовательно как записи
				if len(Entries) > 0:
					for Entry in Entries:
						if WritingEntry:
							self.FinalizeEntry('', CurrentEntry)
						#если это самая первая запись
						else:
							WritingEntry = True
						CurrentEntry = Entry
			self.FinalizeEntry('', CurrentEntry)
		else:
			#пропускаем название словаря
			self.IdxFile.readline()
			PreviousPosition = 0
			while True:
				#перекодируем из указанной кодировки в utf
				KeyWord = self.IdxFile.readline().decode(\
					self.Options.ModuleEncoding).encode('utf_8')
				if KeyWord != '':
					Position = int(self.IdxFile.readline())
					if PreviousPosition != 0:
						self.FinalizeEntry(PreviousKeyWord,\
							self.InputFile.read(Position-PreviousPosition))
					else:
						self.InputFile.read(Position)
					PreviousPosition = Position
					PreviousKeyWord = KeyWord
				else:
					break
			#последняя запись
			self.FinalizeEntry(PreviousKeyWord, self.InputFile.read())
		#запись .conf-файла
		self.ConfFile.write('['+self.DictionaryName+']\n')
		self.ConfFile.write('DataPath=./modules/lexdict/rawld/'+\
			self.DictionaryName+'/dict\n')
		self.ConfFile.write('ModDrv=RawLD4\n')
		self.ConfFile.write('Encoding=UTF-8\n')
		self.ConfFile.write('CompressType=LZSS\n')
		self.ConfFile.write('SourceType=TEI\n')
		self.ConfFile.write('Description='+self.DictionaryName+'.'+\
			self.Options.ModuleLanguage+'\n')
		self.ConfFile.write('Lang='+self.Options.ModuleLanguage+'\n')
		if self.Options.DictionaryType == 'HebrewStrong':
			self.ConfFile.write('Feature=HebrewDef\n')
		elif self.Options.DictionaryType == 'GreekStrong':
			self.ConfFile.write('Feature=GreekDef\n')
		#закрытие файлов
		self.TEIFile.write('\t</body>\n')
		self.TEIFile.write('</text>\n')
		self.TEIFile.write('</TEI>\n')
		self.InputFile.close()
		self.TEIFile.close()
		self.ConfFile.close()
		#выполняем сборку готового модуля для Sword
		TextPath = self.OutputDirectory+'modules/lexdict/rawld/'+\
				self.DictionaryName+'/'
		if not os.path.exists(TextPath):
			os.makedirs(TextPath)
		self.CopyImages(TextPath)
		try:
			TEI2modResult = subprocess.call('tei2mod "'+TextPath+'" "'+\
				self.TEIFileName+'"', shell=True)
			if TEI2modResult < 0:
				print ("tei2mod завершил работу некорректно, ошибка").\
					decode('utf-8'), -retcode
			else:
				print ("Конвертирование успешно выполнено.\n").decode('utf-8')
		except OSError, Error:
			print ("Запуск tei2mod не удался:").decode('utf-8'), Error
	
	#запись заголовка TEI-файла (xml-формат для словарей)
	def WriteTEIHeader(self):
		f = self.TEIFile
		f.write('<?xml version="1.0" encoding="utf-8"?>\n')
		f.write('<TEI xmlns="http://www.crosswire.org/2008/TEIOSIS/namespace"\n')
		f.write('\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
		f.write('\txsi:schemaLocation="http://www.crosswire.org/2008/TEIOSIS/'
			'namespace\n')
		f.write('\thttp://www.crosswire.org/OSIS/teiP5osis.1.4.xsd">\n')
		f.write('<teiHeader>\n')
		f.write('\t<fileDesc>\n')
		f.write('\t\t<titleStmt>\n')
		f.write('\t\t\t<title>'+self.DictionaryName+'</title>\n')
		f.write('\t\t\t<author></author>\n')
		f.write('\t\t</titleStmt>\n')
		f.write('\t\t<editionStmt>\n')
		f.write('\t\t\t<edition></edition>\n')
		f.write('\t\t</editionStmt>\n')
		f.write('\t\t<publicationStmt>\n')
		f.write('\t\t\t<publisher></publisher>\n')
		f.write('\t\t\t<date></date>\n')
		f.write('\t\t</publicationStmt>\n')
		f.write('\t\t<sourceDesc></sourceDesc>\n')
		f.write('\t</fileDesc>\n')
		f.write('\t<revisionDesc>\n')
		f.write('\t\t<change when="'+str(datetime.date.today())+'"></change>\n')
		f.write('\t</revisionDesc>\n')
		f.write('</teiHeader>\n')
		f.write('<text>\n')
		f.write('\t<body>\n')

	def MakeConversion(self):
		print ('bqt2osis, версия '+ScriptVersion+'\n').decode('utf-8')
		print ('Начало процесса преобразования\n').decode('utf-8')
		if self.Options.ModuleType == 'Dictionary':
			self.MakeConversionToTEI()
			return
		if self.Options.ConvertVersification == True:
			self.Options.Versification = 'KJV'
		self.INIFile = file(self.Options.InputFileName, 'r')
		self.ParseINI()
		#закончив разбор INI-файла мы по совместительству закончили разбор всех
		#глав, на которые этот INI-файл ссылался. То есть закончили
		#конвертирование за исключением записи conf-файла и закрытия Osis-файла.
		#Далее это и делаем.
		self.OsisFile.write('</osisText>\n')
		self.OsisFile.write('</osis>\n')
		#записываем conf-файл
		if self.Options.Versification == 'Auto' and\
			not self.Options.ModuleType in self.JustBooks:
			self.Options.Versification = 'Synodal'
			print ('ПРЕДУПРЕЖДЕНИЕ: не удалось определить версификацию'
				' автоматически. Будет использована Synodal\n').decode('utf-8')
		self.WriteConfFile()		
		#закрываем файлы
		self.OsisFile.close()
		self.INIFile.close()
		self.ConfFile.close()
		#выполняем сборку готового модуля для Sword
		TextPath = self.OutputDirectory+self.DataPath+\
				self.HeadBibleShortName+'/'
		if not os.path.exists(TextPath):
			os.makedirs(TextPath)
		self.CopyImages(TextPath)
		try:
			if self.Options.ModuleType in self.JustBooks:
				Osis2modResult = subprocess.call('xml2gbs "'+\
					self.OsisFileName+'" "'+TextPath+self.HeadBibleShortName+\
					'/"', shell=True)
			else:
				Osis2modResult = subprocess.call('osis2mod "'+TextPath+'" "'+\
					self.OsisFileName+'" -z -v '+self.Options.Versification,\
					shell=True)
			if Osis2modResult < 0:
				print ("osis2mod (xml2gbs) завершил работу некорректно, ошибка")\
					.decode('utf-8'), -retcode
			else:
				print ("Конвертирование успешно выполнено.\n").decode('utf-8')
		except OSError, Error:
			print ("Запуск osis2mod не удался:").decode('utf-8'), Error

	# разбор bibleqt.ini
	def ParseINI(self):
		self.IntroductionExist = False
		self.StrongsExist = False
		GeneralSettingsParsed = False
		for Line in self.INIFile:
			# перекодируем строки в UTF-8
			Line = Line.decode(self.Options.INIEncoding).encode('utf_8')
			# обработка основных параметров модуля
			if not GeneralSettingsParsed:
				GeneralSettingsParsed = self.ParseGeneralSettings(Line)
			else:
				# обработка параметров конкретной книги модуля
				self.ParseBookSettings(Line)

	def CheckModuleName(self,Name):
		for i in xrange(0, len(Name)):
			if not Name[i] in string.printable:
				print ('ПРЕДУПРЕЖДЕНИЕ: имя модуля содержит нелатинские\n'
					'символы. Итоговый модуль Sword не будет работать\n'
					'в некоторых фронтендах. Например BibleTime.\n').\
					decode('utf-8')
				return
				
	def ParseGeneralSettings(self, Line):
		# название модуля и короткое название
		if Line.startswith('BibleName'):
			self.HeadBibleName = Line.split('=')[1].lstrip().rstrip()
			return False
		if Line.startswith('BibleShortName'):
			self.HeadBibleShortName=Line.split('=')[1].lstrip().rstrip()
			self.CheckModuleName(self.HeadBibleShortName)
			if self.Options.ModuleType == 'Apocrypha':
				self.HeadBibleShortName += '-Apocrypha'
			# osis-файл с текстом модуля и conf-файл с информацией для Sword
			self.OsisFileName = self.OutputDirectory+self.HeadBibleShortName+\
				'.xml'
			self.OsisFile = file(self.OsisFileName, 'w')
			self.ConfFile=file(self.ConfFileDirectory+\
				self.HeadBibleShortName+'.conf', 'w')
			return False
		# начинается ли в модуле исчисление глав с нуля
		if Line.startswith('ChapterZero') and\
			Line.split('=')[1].lstrip().rstrip() == 'Y':
			self.IntroductionExist = True
			self.OsisWriter.RemakeVersificationProblems()
			return False
		# считываем признак начала главы в HTML файле
		if Line.startswith('ChapterSign'):
			self.BookChapterSign = Line.split('=')[1].lstrip().rstrip()
			return False
		#считываем признак начала стиха
		if Line.startswith('VerseSign'):
			self.BookVerseSign = Line.split('=')[1].lstrip().rstrip()
			return False
		#выводим сообщение о том, что программа не обрабатывает апокрифы
		if Line.startswith('Apocrypha') and\
			Line.split('=')[1].lstrip().rstrip() == 'Y' and\
			not self.Options.ModuleType == 'Apocrypha':
			print ('Скрипт не обрабатывает апокрифы, в связи с тем, что на').\
				decode('utf-8')
			print ('данный момент библиотека Sword не поддерживает апокрифы').\
				decode('utf-8')
			print ('в библейских модулях. Если вам все же нужны апокрифы, то').\
				decode('utf-8')
			print ('запустите скрипт с параметром "--moduletype Apocrypha", ').\
				decode('utf-8')
			print ('чтобы получить модуль, содержащий только апокрифы в'
				' формате').decode('utf-8')
			print ('обычной книги.').decode('utf-8')
			return False
		# определяем наличие в модуле номеров Стронга
		if Line.startswith('StrongNumbers') and\
			Line.split('=')[1].lstrip().rstrip() == 'Y' and\
			not self.Options.ModuleType in self.JustBooks:
			self.StrongsExist = True
			return False		
		#считываем количество книг
		if Line.startswith('BookQty'):
			self.WriteHeadOsis()  #печатаем заголовок osis файла
			return True
			
	def ParseBookSettings(self, Line):
		#считываем имя файла, относительно текущей директории
		if Line.startswith('PathName'):
			self.CurrentBookSettings.BookPathToFile = self.BQModuleDirectory+\
				Line.split('=')[1].lstrip().rstrip()
			return
		#ищем соответвие длинного названия книги и короткого
		if Line.startswith('ShortName') and self.Options.ModuleType != 'Book':
			for Pair in self.TableBooks:
				if Pair[0] in Line:
					self.CurrentBookSettings.BookName = Pair[1]
					self.CurrentBookSettings.Testament = Pair[2]
					if Pair[2] == 3 and\
						not self.Options.ModuleType == 'Apocrypha':
						print ('ПРЕДУПРЕЖДЕНИЕ: '+\
							self.CurrentBookSettings.BookName+\
							' - апокрифическая книга. Будет пропущена.').\
							decode('utf-8')
						self.CurrentBookSettings.BookName = ''
					elif Pair[2]!=3 and self.Options.ModuleType == 'Apocrypha':
						print ('ПРЕДУПРЕЖДЕНИЕ: '+\
							self.CurrentBookSettings.BookName+\
							' - каноническая книга. Будет пропущена.').\
							decode('utf-8')
						self.CurrentBookSettings.BookName = ''
					break
				if Pair == self.TableBooks[len(self.TableBooks)-1]:
					self.CurrentBookSettings.BookName = ''
					print ('Ошибка, не найдено название книги "'+Line.split('=')\
						[1].lstrip().rstrip()+'". Будет пропущена.').\
						decode('utf-8')
		#сохраняем название книги
		if Line.startswith('FullName') and self.Options.ModuleType == 'Book':
			self.CurrentBookSettings.BookName = Line.split('=')[1].lstrip().\
				rstrip()
		#переходим к чтению файла книги
		if Line.startswith('ChapterQty') and\
			self.CurrentBookSettings.BookName != '':
			BookFile = file(self.GetFileNameInProperCase(\
				self.CurrentBookSettings.BookPathToFile), 'r')
			print ('Обрабатываю файл ').decode('utf-8')+\
				self.CurrentBookSettings.BookPathToFile
			self.ParseBookFile(BookFile, self.CurrentBookSettings.BookName)
			BookFile.close()

	#класс отвечает за запись данных в Osis-файл, хранение и обработку
	#идентификаторов глав и стихов, а таже за преобразование версификаций
	class COsisWriter:

		def __init__(self, Converter):
			self.Converter = Converter
			self.CurrentVerseId = 0
			self.CurrentChapterId = 0
			self.CurrentBookName = ''
			self.IntroductionMode = False
			#для Даниила отдельный код, потому-что там очень много пропускать
			if self.Converter.Options.ConvertVersification:
				for i in reversed(xrange(24,91)):
					self.VersificationProblems.append(['Dan',3,100+i-90,\
						self.Acts.Delete,3,i])
				for i in reversed(xrange(14,120)):
					self.VersificationProblems.append(['Dan',12,i,\
						self.Acts.Delete,12,i])

		def RemakeVersificationProblems(self):
			#если в книге есть вступления, все номера глав в таблице проблем
			#версификациии надо увеличить на 1
			if self.Converter.Options.ConvertVersification:
				NewProblemsList = []
				for BookName, BadChapterId, VersesCount, Action, ChapterId,\
					VerseId in self.VersificationProblems:
					NewProblemsList.append([BookName, BadChapterId+1,\
						VersesCount, Action, ChapterId+1, VerseId])
				self.VersificationProblems = NewProblemsList
	
		#функции выводят в OsisFile и предоставляет некоторый дополнительный
		#сервис по поддержанию актуальности номеров глав и стихов
		def BeginBook(self, BookName):
			#открыть новый
			self.Book = []
			self.CurrentVerseId = 0
			self.CurrentChapterId = 0
			self.CurrentBookName = BookName

			OsisFile = self.Converter.OsisFile
			OsisFile.write('\n\t\t<div type="book" osisID='+\
				'"'+BookName+'">\n')
		
		def RealWriteVerse(self, BookName, ChapterId, VerseId, Text):
			#записываем текст файл в нужном виде
			OsisFile = self.Converter.OsisFile
			if self.Converter.Options.ModuleType in self.Converter.JustBooks or\
				self.IntroductionMode:
				OsisFile.write('\t\t\t\t<p>')
				OsisFile.write(Text)
				OsisFile.write('</p>\n')
			else:
				if self.Converter.Options.ModuleType == 'Bible':
					OsisFile.write('\t\t\t\t<verse osisID="'+BookName+'.'+\
						str(ChapterId)+'.'+str(VerseId)+'">')
					OsisFile.write(Text)
					OsisFile.write('</verse>\n')
				elif self.Converter.Options.ModuleType == 'Commentary':
					OsisFile.write('\t\t\t\t<div annotateType="commentary"'
						' annotateRef="'+BookName+'.'+\
						str(ChapterId)+'.'+str(VerseId)+'">')
					OsisFile.write(Text)
					OsisFile.write('</div>\n')
		
		def EndBook(self):
			OsisFile = self.Converter.OsisFile
			#закрываем главу
			self.Converter.FinalizeVerse()
			#осуществляем конвертирование версификации
			self.ConvertVersification()
			#записываем книгу в Osis-файл
			for ChapterId, VersesList in self.Book:
				if  self.Converter.IntroductionExist and ChapterId == 1:
					for VerseId, Text in VersesList:
						self.IntroductionMode = True
						self.RealWriteVerse(self.CurrentBookName, ChapterId,\
							VerseId, Text)
						self.IntroductionMode = False
				else:
					if self.Converter.IntroductionExist:
						ChapterId -= 1
					self.Converter.OsisFile.write('\t\t\t<chapter osisID="'+\
						self.CurrentBookName+'.'+str(ChapterId)+'">\n')
					for VerseId, Text in VersesList:
						self.RealWriteVerse(self.CurrentBookName, ChapterId,\
							VerseId, Text)
					OsisFile.write('\t\t\t</chapter>\n')
			#закрываем книгу
			OsisFile.write('\t\t</div>\n')
		
		def BeginChapter(self):
			#закрыть предыдущий элемент
			if self.CurrentChapterId != 0:
				#закрываем главу
				self.Converter.FinalizeVerse()
			#открыть новый
			self.CurrentChapterId += 1
			self.CurrentVerseId = 0
			self.Book.append((self.CurrentChapterId, []))		
		
		#определяем VerseId
		def DetermineVerseId(self, SuggestedVerseId):
			if SuggestedVerseId == -1:
				print ("ПРЕДУПРЕЖДЕНИЕ: Стих без номера вначале. "+\
					self.CurrentBookName+'.'+str(self.CurrentChapterId)+'.'+\
					str(self.CurrentVerseId)+'\r').decode('utf-8')
			elif SuggestedVerseId != self.CurrentVerseId:
				print ("ПРЕДУПРЕЖДЕНИЕ: Несоответствие нумерации. Должен быть "\
					+self.CurrentBookName+'.'+str(self.CurrentChapterId)+'.'+\
					str(self.CurrentVerseId)+', встретили '+\
					self.CurrentBookName+'.'+str(self.CurrentChapterId)+'.'+\
					str(SuggestedVerseId)+'\r').decode('utf-8')
				self.CurrentVerseId = SuggestedVerseId

		def DetermineVersification(self):
			if ((self.CurrentBookName == 'Ps' and self.CurrentChapterId == 9\
				and self.CurrentVerseId == 39) or\
				(self.CurrentBookName == 'Rom' and self.CurrentChapterId == 14\
				and self.CurrentVerseId == 26)):
				self.Converter.Options.Versification = 'Synodal'
			if ((self.CurrentBookName == 'Ps' and self.CurrentChapterId == 10\
				and self.CurrentVerseId == 18) or\
				(self.CurrentBookName == 'Acts' and self.CurrentChapterId == 19\
				and self.CurrentVerseId == 41)):
				self.Converter.Options.Versification = 'KJV'

		def WriteVerse(self, Text, SuggestedVerseId):
			#определяем VerseId
			self.DetermineVerseId(SuggestedVerseId)
			#автоматическое определение версификации
			if self.Converter.Options.Versification == 'Auto':
				self.DetermineVersification()
			#добавляем заголовки и сноски
			Text = self.Converter.MakeNotesAndTitles(Text,self.CurrentBookName,\
				self.CurrentChapterId, self.CurrentVerseId)
			self.Book[-1][1].append((self.CurrentVerseId, Text))
			
		#преобразование версификации из Synodal в KJV
		class Acts:
			Delete, Append, Split, Join = range(4) 
		
		VersificationProblems=[
		#проблемы версификации и способы их решения описываются данной таблицей
		#сначала следует указание проблемы в виде книги, главы и количества
		#стихов в ней, которое не соответствует версификации KJV, программа
		#проверит количество стихов в каждой главе и если оно не совпадает с
		#проблемным, ничего не будет предпринято. Если же наблюдается совпадение,
		#выполняется действие соответствующее данной проблеме в таблице
		#действия: удалить указанный стих, склеить с предыдущим, вставить после
		#стиха разрыв главы, убрать разрыв главы, идущий после данного стиха
		['Ps',		3,		9,		Acts.Append,		3,		2],
		['Ps',		4,		9,		Acts.Append,		4,		2],
		['Ps',		5,		13,		Acts.Append,		5,		2],
		['Ps',		6,		11,		Acts.Append,		6,		2],
		['Ps',		7,		18,		Acts.Append,		7,		2],
		['Ps',		8,		10,		Acts.Append,		8,		2],
		['Ps',		9,		39,		Acts.Append,		9,		2],
		['Ps',		9,		38,		Acts.Split,			9,		20],
		['Ps',		12,		9,		Acts.Append,		12,		2],
		['Ps',		13,		7,		Acts.Append,		13,		2],
		['Ps',		18,		51,		Acts.Append,		18,		2],
		['Ps',		19,		15,		Acts.Append,		19,		2],
		['Ps',		20,		10,		Acts.Append,		20,		2],
		['Ps',		21,		14,		Acts.Append,		21,		2],
		['Ps',		22,		32,		Acts.Append,		22,		2],
		['Ps',		30,		13,		Acts.Append,		30,		2],
		['Ps',		31,		25,		Acts.Append,		31,		2],
		['Ps',		34,		23,		Acts.Append,		34,		2],
		['Ps',		36,		13,		Acts.Append,		36,		2],
		['Ps',		38,		23,		Acts.Append,		38,		2],
		['Ps',		39,		14,		Acts.Append,		39,		2],
		['Ps',		40,		18,		Acts.Append,		40,		2],
		['Ps',		41,		14,		Acts.Append,		41,		2],
		['Ps',		42,		12,		Acts.Append,		42,		2],
		['Ps',		44,		27,		Acts.Append,		44,		2],
		['Ps',		45,		18,		Acts.Append,		45,		2],
		['Ps',		46,		12,		Acts.Append,		46,		2],
		['Ps',		47,		10,		Acts.Append,		47,		2],
		['Ps',		48,		15,		Acts.Append,		48,		2],
		['Ps',		49,		21,		Acts.Append,		49,		2],
		['Ps',		51,		21,		Acts.Append,		51,		2],
		['Ps',		51,		20,		Acts.Append,		51,		2],
		['Ps',		52,		11,		Acts.Append,		52,		2],
		['Ps',		52,		10,		Acts.Append,		52,		2],
		['Ps',		53,		7,		Acts.Append,		53,		2],
		['Ps',		54,		9,		Acts.Append,		54,		2],
		['Ps',		54,		8,		Acts.Append,		54,		2],
		['Ps',		55,		24,		Acts.Append,		55,		2],
		['Ps',		56,		14,		Acts.Append,		56,		2],
		['Ps',		57,		12,		Acts.Append,		57,		2],
		['Ps',		58,		12,		Acts.Append,		58,		2],
		['Ps',		59,		18,		Acts.Append,		59,		2],
		['Ps',		60,		14,		Acts.Append,		60,		2],
		['Ps',		60,		13,		Acts.Append,		60,		2],
		['Ps',		61,		9,		Acts.Append,		61,		2],
		['Ps',		62,		13,		Acts.Append,		62,		2],
		['Ps',		63,		12,		Acts.Append,		63,		2],
		['Ps',		64,		11,		Acts.Append,		64,		2],
		['Ps',		65,		14,		Acts.Append,		65,		2],
		['Ps',		67,		8,		Acts.Append,		67,		2],
		['Ps',		68,		36,		Acts.Append,		68,		2],
		['Ps',		69,		37,		Acts.Append,		69,		2],
		['Ps',		70,		6,		Acts.Append,		70,		2],
		['Ps',		75,		11,		Acts.Append,		75,		2],
		['Ps',		76,		13,		Acts.Append,		76,		2],
		['Ps',		77,		21,		Acts.Append,		77,		2],
		['Ps',		80,		20,		Acts.Append,		80,		2],
		['Ps',		81,		17,		Acts.Append,		81,		2],
		['Ps',		83,		19,		Acts.Append,		83,		2],
		['Ps',		84,		13,		Acts.Append,		84,		2],
		['Ps',		85,		14,		Acts.Append,		85,		2],
		['Ps',		88,		19,		Acts.Append,		88,		2],
		['Ps',		89,		53,		Acts.Append,		89,		2],
		['Ps',		92,		16,		Acts.Append,		92,		2],
		['Ps',		102,	29,		Acts.Append,		102,	2],
		['Ps',		108,	14,		Acts.Append,		108,	2],
		['Ps',		114,	26,		Acts.Split,			114,	8],
		['Ps',		116,	9,		Acts.Join,			116,	9],
		['Ps',		140,	14,		Acts.Append,		140,	2],
		['Ps',		147,	11,		Acts.Join,			147,	11],
		['Num',		12,		15,		Acts.Join,			12,		15],
		['Num',		12,		49,		Acts.Split,			12,		16],
		['Num',		29,		39,		Acts.Join,			29,		39],
		['Num',		29,		56,		Acts.Split,			29,		40],
		['Josh',	5,		16,		Acts.Split,			5,		15],
		['Josh',	6,		1,		Acts.Join,			6,		1],
		['Josh',	24,		36,		Acts.Delete,		24,		36],
		['Josh',	24,		35,		Acts.Delete,		24,		35],
		['Josh',	24,		34,		Acts.Delete,		24,		34],
		['1Sam',	23,		28,		Acts.Join,			23,		28],
		['1Sam',	23,		51,		Acts.Split,			23,		29],
		['2Chr',	36,		24,		Acts.Delete,		36,		24],
		['Job',		39,		35,		Acts.Split,			39,		30],
		['Job',		40,		5,		Acts.Join,			40,		5],
		['Job',		40,		32,		Acts.Split,			40,		24],
		['Job',		41,		8,		Acts.Join,			41,		8],
		['Job',		42,		18,		Acts.Delete,		42,		18],
		['Prov',	4,		29,		Acts.Delete,		4,		29],
		['Prov',	4,		28,		Acts.Delete,		4,		28],
		['Prov',	13,		26,		Acts.Delete,		13,		14],
		['Prov',	18,		25,		Acts.Delete,		18,		8],
		['Eccl',	4,		17,		Acts.Split,			4,		16],
		['Eccl',	5,		1,		Acts.Join,			5,		1],
		['Song',	6,		12,		Acts.Join,			6,		12],
		['Song',	6,		26,		Acts.Split,			6,		13],
		['Dan',		13,		64,		Acts.Join,			12,		13],
		['Dan',		13,		42,		Acts.Join,			12,		77],
		['Hos',		13,		15,		Acts.Join,			13,		15],
		['Hos',		13,		25,		Acts.Split,			13,		16],

		['Jonah',	1,		16,		Acts.Join,			1,		16],
		['Jonah',	1,		27,		Acts.Split,			1,		17],
		]
		def FixVersificationProblem(self, Action, ChapterId, VerseId):
			if Action == self.Acts.Append:
				VerseList = self.Book[ChapterId-1][1]
				#добавляем к тексту первого стиха текст второго
				VerseList[VerseId-2]=(VerseList[VerseId-2][0],\
					VerseList[VerseId-2][1]+VerseList[VerseId-1][1])
				#удаляем ненужный второй
				del VerseList[VerseId-1]
				#корректируем номера у всех последующих стихов
				for i in xrange(VerseId-1,len(VerseList)):
					VerseList[i] = (VerseList[i][0]-1, VerseList[i][1])
			if Action == self.Acts.Split:
				#делаем новую главу со стихами, идущими за данным
				OldChapter = self.Book[ChapterId-1]
				self.Book[ChapterId:ChapterId] = [(OldChapter[0]+1,\
					OldChapter[1][VerseId:])]
				#увеличиваем у всех последующих глав номер на 1
				for i in xrange(ChapterId+1,len(self.Book)):
					self.Book[i] = (self.Book[i][0]+1,self.Book[i][1])
				#корректируем номера стихов у новоявленной главы
				VerseList = self.Book[ChapterId][1]
				for i in xrange(0,len(VerseList)):
					VerseList[i] = (VerseList[i][0]-VerseId, VerseList[i][1])
				#удаляем ставшие ненужными стихи старой главы
				self.Book[ChapterId-1]=(OldChapter[0],OldChapter[1][:VerseId])
			if Action == self.Acts.Join:
				#корректируем номера стихов у присоединяемой главы
				VerseList = self.Book[ChapterId][1]
				for i in xrange(0,len(VerseList)):
					VerseList[i] = (VerseList[i][0]+VerseId, VerseList[i][1])
				#склеиваем главы
				self.Book[ChapterId-1] = (self.Book[ChapterId-1][0],\
					self.Book[ChapterId-1][1]+self.Book[ChapterId][1])
				#удаляем ненужную главу
				del self.Book[ChapterId]
				#уменьшаем у всех последующих глав номер на 1
				for i in xrange(ChapterId,len(self.Book)):
					self.Book[i] = (self.Book[i][0]-1,self.Book[i][1])
			if Action == self.Acts.Delete:
				VerseList = self.Book[ChapterId-1][1]
				#удаляем ненужный второй
				del VerseList[VerseId-1]
				#корректируем номера у всех последующих стихов
				for i in xrange(VerseId-1,len(VerseList)):
					VerseList[i] = (VerseList[i][0]-1, VerseList[i][1])
				
		def ConvertVersification(self):
			if not self.Converter.Options.ConvertVersification:
				return
			#для каждой проблемы и каждой главы книги если адреса совпадают
			ProblemFound = True
			while ProblemFound:
				ProblemFound = False
				for BookName, BadChapterId, VersesCount, Action, ChapterId,\
					VerseId in self.VersificationProblems:
					for CurrentChapterId, VersesList in self.Book:
						if not ProblemFound and BookName ==\
							self.CurrentBookName and BadChapterId ==\
							CurrentChapterId and VersesCount ==\
							VersesList[-1][0]:
							ProblemFound = True
							self.FixVersificationProblem(Action, ChapterId,\
								VerseId)
							
							

	#разбор одного файла - книги			
	def ParseBookFile(self, BookFile, BookName):
		#стих начинает набираться заново и в новой главе нумерация сначала
		self.CurrentBookSettings.CurrentVerse = ''
		#нумерация сносок сквозная в рамках одной книги
		self.CurrentBookSettings.NoteNumber = 1
		#начинаем книгу
		self.OsisWriter.BeginBook(BookName)
		for Line in BookFile:
			#перекодируем из указанной кодировки в utf
			Line = Line.decode(self.Options.ModuleEncoding).encode('utf_8')
			#разбиваем строку на блоки, разделенные признаком конца главы
			PreparsedLine = Line.split(self.BookChapterSign, 1)
			#первый блок записываем в конец текущей главы
			if len(PreparsedLine) > 0 and self.OsisWriter.CurrentChapterId != 0:
				self.ParseChapter(PreparsedLine[0])
				PreparsedLine = PreparsedLine[1:]
			elif self.OsisWriter.CurrentChapterId == 0:
				PreparsedLine = PreparsedLine[1:]
			#остальные блоки записываем последовательно как главы
			if len(PreparsedLine) > 0:
				for Chapter in PreparsedLine:
					#начинаем новую главу
					self.OsisWriter.BeginChapter()
					#собственно обработка содержимого главы
					self.ParseChapter(Chapter)
		self.OsisWriter.EndBook()

	#разбор главы или куска главы с записью стихов в выходной файл
	def ParseChapter(self, Line):
		#разбиваем строку на блоки, разделенные признаком конца стиха
		PreparsedLine = Line.split(self.BookVerseSign)
		#первый блок записываем в конец текущего стиха
		if len(PreparsedLine) > 0 and self.OsisWriter.CurrentVerseId >= 1:
			self.CurrentBookSettings.CurrentVerse += PreparsedLine[0]
			PreparsedLine = PreparsedLine[1:]
		elif self.OsisWriter.CurrentVerseId < 1:
			PreparsedLine = PreparsedLine[1:]
		#остальные блоки записываем последовательно как стихи
		if len(PreparsedLine) > 0:
			for Verse in PreparsedLine:
				if self.CurrentBookSettings.CurrentVerse != '':
					self.FinalizeVerse()
				self.CurrentBookSettings.CurrentVerse += Verse
				self.OsisWriter.CurrentVerseId += 1
	
	#добавление заголовков и сносок
	def MakeNotesAndTitles(self, Text, BookName, ChapterId, VerseId):
		#сноски
		if self.Options.NoteTag != '':
			NoteNumber = self.CurrentBookSettings.NoteNumber
			NewText = Text.replace('<i>', '<note type="explanation" osisRef="'+\
				BookName+'.'+str(ChapterId)+'.'+str(VerseId)+'" n="'+\
				str(NoteNumber)+'">', 1)
			#пробегаем по всем сноскам в стихе, когда очередной проход перестает
			#изменять текст, значит сноски кончились
			while NewText != Text:
				Text = NewText
				NoteNumber = NoteNumber+1
				NewText = Text.replace('<i>',\
					'<note type="explanation" osisRef="'+BookName+'.'+\
					str(ChapterId)+'.'+str(VerseId)+'" n="'+str(NoteNumber)+\
					'">', 1)
			Text = Text.replace('</i>', '</note>')
			self.CurrentBookSettings.NoteNumber = NoteNumber
		#заголовки
		if self.Options.TitleTag != '':
			Text = Text.replace('<b>',\
				'<title canonical="true" subType="x-preverse" type="section">')
			Text = Text.replace('</b>', '</title>')
		return Text
	
	#удаление лишних пробелов
	def RemoveDoubleSpaces(self, Text):
		Expression = re.compile(r' [ ]+')
		return Expression.sub(' ', Text)
	
	#дополнение пробелами справа и слева
	def AmplifyWithSpaces(self, Match):
		return ' '+Match.group(0)+' '
	
	#обработка номеров Стронга
	def MakeStrongNumbers(self, Text):
		#знаки препинания, не отделенные пробелами мешают разбить строчку на
		#нужные нам составляющие
		PunctuationSigns = (',','.','?',':',';',')','!','"',"'")
		for Sign in PunctuationSigns:
			Text = Text.replace(Sign, ' '+Sign+' ')
		#добавляем пробелы между номерами стронга и словами (в некоторых особо
		#кривых модулях их нет, но Цитата, тем не менее, с такими номерами
		#как-то работает
		Expression = re.compile(r'[\d]+')
		Text = Expression.sub(self.AmplifyWithSpaces, Text)
		#удаляем лишние пробелы
		Text = self.RemoveDoubleSpaces(Text)
		#теперь разбиваем текст на слова, знаки, теги, номера Стронга
		Verse = Text.split()
		Pairs = []
		#формируем список пар (Слово, [Список соответствующих номеров Стронга])
		for Something in Verse:
			#если это тег, создаем пару и помещаем его в левую часть, в правую
			#кладем некорректный номер
			if Something in ('<i>', '</i>', '<b>', '</b>'):
				Pairs.append([[Something],['']])
			#если это цифра, помещаем его в правую часть последней пары
			elif Something.isdigit() and len(Pairs)>0:
				Pairs[-1][1].append(Something)
			#если это слово, создаем пару и помещаем его в левую часть
			else:
				Pairs.append([[Something],[]])
		#находим случаи перевода одного слова оригинала несколькими словами
		#языка перевода, представляем в виде списка ([слова],[номера])
		i = 1
		while i < len(Pairs)-1:
			if len(Pairs[i][1]) == 0:
				pass
			elif Pairs[i][1][0] == '':
				pass
			elif Pairs[i][1][-1] == '0' and len(Pairs[i-1][1])>0 and\
				Pairs[i-1][1][0] != ''	and Pairs[i-1][1] == Pairs[i][1]:
				Pairs[i-1][0].append(Pairs[i][0][0])
				del Pairs[i]
				i = i-1
			i = i+1
		#формируем результирующую строку
		Output = ''
		for Pair in Pairs:
			if len(Pair[1])>0 and Pair[1][0]!='':
				Output = Output + '<w lemma="'
				#кладем номера Стронга внутри тега
				FirstNumber = True
				for Number in Pair[1]:
					for i in xrange (0, 5-len(Number)):
						Number = '0'+Number
					if not FirstNumber and Number != '0':
						Output = Output + ' '
					if self.CurrentBookSettings.Testament == 1:
						Output = Output + 'strong:H' + Number
					else:
						Output = Output + 'strong:G' + Number
					FirstNumber = False
				#закрываем тег
				Output = Output + '"> ' + str.join(' ', Pair[0]) + '</w>'
			#для слов, которым не соответствуют номера Стронга, тегов и знаков
			else:
				if Pair[0][0] in PunctuationSigns:
					Output = Output + Pair[0][0]
				else:
					Output = Output + ' ' + Pair[0][0]
		return Output

	#перевод текста к правильному набору символов. Нужно поскольку некоторые
	#модули используют для отображения некоторых языков (греческого, например)
	#шрифты с расположением символов, не соответствующим ASCII
	def StripTagsAndRecode(self, Text):
		self.HTMLParser.Result = ''
		try:
			self.HTMLParser.feed(Text)
			self.HTMLParser.close()
		#если стих не является корректным HTML, просто удаляем из него все, что
		#похоже на теги
		except:
			Expression = re.compile(r'<[^<>]*>')
			Text = Expression.sub('', Text)
			self.HTMLParser.reset()
			self.HTMLParser.feed(Text)
			self.HTMLParser.close()
		return self.HTMLParser.Result

	#записываем текст стиха предварительно очистив его от тегов и прочего мусора
	def FinalizeVerse(self):
		Text = self.CurrentBookSettings.CurrentVerse
		#убираем переводы строки
		Text = Text.replace('\r',' ')
		Text = Text.replace('\n',' ')
		#переводим текст в правильный набор символов
		Text = self.StripTagsAndRecode(Text)
		#вычисление VerseId по первому числу стиха
		if self.Options.ModuleType in self.JustBooks:
			Number = self.OsisWriter.CurrentVerseId
		else:
			try:
				Text = Text.lstrip()
				NumberText = ''
				#определяем номер стиха
				for i in xrange(0, len(Text)):
					if Text[i].isdigit():
						NumberText += Text[i]
					else:
						break
				Number = int(NumberText)
				#убираем номер стиха из самого текста
				Text = Text[i:]
			except (IndexError, ValueError):
				Number = -1
		#обработка стронгов
		if self.StrongsExist:
			Text = self.MakeStrongNumbers(Text)
		#удаляем лишние пробелы
		Text = self.RemoveDoubleSpaces(Text)
		#собственно запись
		self.OsisWriter.WriteVerse(Text, Number)
		#обнуляем накопленный стих и возвращаем текущий номер
		self.CurrentBookSettings.CurrentVerse = ''

	# запись заголовка Osis-файла
	def WriteHeadOsis(self):
		f = self.OsisFile
		f.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
		f.write('<osis \n xmlns="http://www.bibletechnologies.net/'
			'2003/OSIS/namespace" \n xmlns:xsi="http://www.w3.org/2001/'
			'XMLSchema-instance" \n xsi:schemaLocation="http://www.'
			'bibletechnologies.net/2003/OSIS/namespace osisCore.2.5.xsd">\n')
		if self.Options.ModuleType in self.JustBooks:
			f.write('<osisText osisIDWork="'+self.HeadBibleShortName+'-'+\
				self.Options.ModuleLanguage+\
				'" osisRefWork="book" xml:lang="'+\
				self.Options.ModuleLanguage+'">\n')
		else:
			f.write('<osisText osisIDWork="'+self.HeadBibleShortName+'-'+\
				self.Options.ModuleLanguage+\
				'" osisRefWork="defaultReferenceScheme" xml:lang="'+\
				self.Options.ModuleLanguage+'">\n')
		f.write('\t<header>\n')
		f.write('\t\t<work osisWork=\"'+self.Options.ModuleType+'-'+\
			self.HeadBibleShortName+'.'+self.Options.ModuleLanguage+'\">\n')
		f.write('\t\t\t<title>'+self.HeadBibleName+'</title>\n')
		f.write('\t\t\t<identifier type="OSIS">'+self.Options.ModuleType+'-'+\
			self.HeadBibleShortName+'.'+self.Options.ModuleLanguage+\
			'</identifier>\n')
		f.write('\t\t\t<refSystem>'+self.Options.ModuleType+'-'+\
			self.HeadBibleShortName+'</refSystem>\n')
		f.write('\t\t</work>\n')
		f.write('\t\t<work osisWork="defaultReferenceScheme">\n')
		f.write('\t\t\t<refSystem>'+self.Options.ModuleType+'-'+\
			self.HeadBibleShortName+'</refSystem>\n')
		f.write('\t\t</work>\n')
		if self.StrongsExist:
			f.write('\t\t<work osisWork="strong">\n')
			f.write('\t\t\t<refSystem>Dict.Strongs</refSystem>\n')
			f.write('\t\t</work>\n')
		f.write('\t</header>\n')
		f.write('\t<div type="x-testament">')

	def WriteConfFile(self):
		f = self.ConfFile
		f.write('['+self.HeadBibleShortName+']\n')
		if self.Options.ModuleType in self.JustBooks:
			f.write('DataPath=./'+self.DataPath+self.HeadBibleShortName+'/'+\
				self.HeadBibleShortName+'\n')
		else:
			f.write('DataPath=./'+self.DataPath+self.HeadBibleShortName+'/\n')
		if self.Options.ModuleType == 'Bible':
			f.write('ModDrv=zText\n')
		elif self.Options.ModuleType == 'Commentary':
			f.write('ModDrv=zCom\n')
		elif self.Options.ModuleType in self.JustBooks:
			f.write('ModDrv=RawGenBook\n')
		if not self.Options.ModuleType in self.JustBooks:
			f.write('BlockType=BOOK\n')
			f.write('CompressType=ZIP\n')
			f.write('Versification='+self.Options.Versification+'\n')
		f.write('Encoding=UTF-8\n')
		f.write('SourceType=OSIS\n')
		f.write('Description='+self.HeadBibleShortName+'.'+\
			self.Options.ModuleLanguage+'\n')
		f.write('Lang='+self.Options.ModuleLanguage+'\n')
		if self.Options.NoteTag != '':
			f.write('GlobalOptionFilter=OSISFootnotes\n')
		if self.Options.TitleTag != '':
			f.write('GlobalOptionFilter=OSISHeadings\n')
		if self.StrongsExist:
			f.write('GlobalOptionFilter=OSISStrongs\n')

	# необходимо для систем, чуствительных к регистру в имени файла 
	# (например Linux). Функция возвращает имя файла в правильном регистре,
	# определяя его в соответствии со списком файлов в директории
	def GetFileNameInProperCase(self, InFileName):
		FilesList=os.listdir(os.path.dirname(InFileName))
		FileNameInLowCase=os.path.basename(InFileName).lower();
		for FileName in FilesList:
			if os.path.basename(FileName).lower()==FileNameInLowCase:
				return os.path.dirname(InFileName)+'/'+FileName
		return InFileName

# если скрипт запущен из командной строки
if __name__=='__main__':
	#определение кодировки
	if sys.stdout.encoding == None:
		reload(sys)
		sys.setdefaultencoding('utf-8')
	#опции вызова скрипта
	from optparse import OptionParser, OptionGroup
	Parser = OptionParser(usage="Usage: %prog [options] InputFile")
	Parser.add_option('--moduletype', dest='ModuleType',\
		default='Bible', help=('тип модуля. Допустимые значения: '
		'Bible (по умолчанию), Dictionary, Commentary, Book, Apocrypha. '
		'Dictionary для словаря (поскольку у словарей нет bibleqt.ini, в '
		'качестве входного нужно указывать .htm-файл со словарем), Commentary'
		' для комментария, Book для просто книги, Bible для библии. О типе '
		'Apocrypha. Можно увидеть на примере модуля "Русский синодальный '
		'текст (с номерами Стронга)". Этот модуль содержит апокрифы, но Sword'
		' апокрифы в библиях не поддерживает. Поэтому если вы запустите на '
		'нем скрипт без указания --moduletype (он по умолчанию Bible), то '
		'получите библейский модуль со всеми каноническими книгами. А если '
		'запустите на нем же с --moduletype Apocrypha, то получите модуль '
		'типа "просто книга" с только лишь апокрифическими книгами.').\
		decode('utf-8'), choices=['Bible', 'Dictionary', 'Commentary', 'Book',\
		'Apocrypha'], type='choice')
	GeneralModuleGroup = OptionGroup(Parser, ('Опции, общие для всех модулей').\
		decode('utf-8'))
	GeneralModuleGroup.add_option('--op','--outputpath', dest='OutputPath',\
		default='convertoutput/',\
		help=('выходная папка. По умолчанию: convertoutput/').decode('utf-8'))             
	GeneralModuleGroup.add_option('--l','--language', dest='ModuleLanguage',\
		default='ru', help=('язык модуля. По умолчанию: ru').decode('utf-8'))
	GeneralModuleGroup.add_option('--cs','--charset', dest='CharsetName',\
		default='',\
		help=('основной шрифт, используемый в модуле. Необходимо только если'
		' используется шрифт, в котором расположение символов не совпадает с'
		' ни с одной стандартной кодировкой (например некоторые'
		' греческие и еврейские шрифты). Можно определить открыв какой-нибудь'
		' .htm-файл модуля в текстовом редакторе (например, Блокнот). Если '
		'там, где в Цитате наблюдается греческий, еврейский или еще какой-'
		'нибудь не латинский текст, вы видите набор латинских символов и '
		'знаков препинания, значит в этом месте применен такой шрифт. Данную '
		'опцию надо использовать лишь, если весь текст в модуле набран таким '
		'образом. В комплекте с программой содержатся таблицы перекодировки '
		'для наиболее распространенных шрифтов: Symbol, BQTGrk, BQTHeb. В '
		'качестве примера можно посмотреть модуль "Greek-Westcott Hort". '
		'Он весь набран с использованием греческого шрифта Symbol. Для него '
		'подходит опция --cs Symbol').decode('utf-8'))
	GeneralModuleGroup.add_option('--eb','--encodingbooks',\
		dest='ModuleEncoding', default='cp1251', help=(\
		'кодировка модуля BibleQuote. По умолчанию: cp1251').decode('utf-8'))
	GeneralModuleGroup.add_option('--lbt','--linebreaktag',\
		dest='LineBreakTag', default='', help=(\
		'тег разрыва строки. Чаще всего в модулях непарный тег br '
		'(указывается как --linebreaktag br). Используется почти во всех '
		'модулях, но не для всех модулей целесообразно его указывать при '
		'конвертировании. В большинстве модулей перевод строки стоит к месту '
		'и не к месту и его перенос в модуль Sword приводит к тому, что на '
		'экране модуль смотрится неряшливо. А для некоторых модулей, если не '
		'делать перевода строки, то получается очень трудночитаемый текст. '
		'Таков, например, словарь Zondervan. Нужно подходить к делу творчески'
		', оценивая конечный результат (внешний вид модуля в Sword)').\
		decode('utf-8'))
	Parser.add_option_group(GeneralModuleGroup)
	NonDictionaryModuleGroup = OptionGroup(Parser, ('Опции, общие для всех'
		' модулей, кроме словарей').decode('utf-8'))
	NonDictionaryModuleGroup.add_option('--e','--encoding', dest='INIEncoding',\
		default='cp1251',\
		help=('кодировка bibleqt.ini. По умолчанию: cp1251').decode('utf-8'))
	Parser.add_option_group(NonDictionaryModuleGroup)
	BibleModuleGroup = OptionGroup(Parser, ('Опции, общие для библейских'
		' модулей').decode('utf-8'))
	BibleModuleGroup.add_option('--v','--versification', dest='Versification',\
		default='Auto', help=(\
		'версификация. Разные библейские модули используют разные стандарты'
		' по разбиению текста на главы и стихи. Если не указана, программа '
		'попробует определить ее автоматически. Если в 9-м псалме есть 39-й'
		' стих или в 14-й главе послания Римлянам есть 36-й стих, будет '
		'принята Synodal. Если в 10-м псалме есть 18-й стих или в 19-й главе'
		' Деяний есть 41-й стих, будет принята KJV. Если определить '
		'версификацию автоматически не удастся, будет выдано соответствующее '
		'предупреждение и принята версификация Synodal').decode('utf-8'))
	BibleModuleGroup.add_option('--cv','--convertversification',\
		action="store_true",dest='ConvertVersification',help=(\
		'преобразовывать из Synodal версификации в KJV. Скрипт произведет '
		'переразбивку глав в соответствии с нужной версификацией').\
		decode('utf-8'))
	BibleModuleGroup.add_option('--nt','--notetag', dest='NoteTag', default='',\
		help=('тег, отделяющий сноски от текста в модуле BibleQuote.').\
		decode('utf-8'))
	BibleModuleGroup.add_option('--tt','--titletag', dest='TitleTag',default='',\
		help=('тег, отделяющий подзаголовки от текста в модуле BibleQuote.'
		' Нужно открыть модуль в Цитате и посмотреть, есть ли там в тексте '
		'блоки с отличным от обычного форматированием (заголовки жирным '
		'текстом или сноски курсивом), затем открыть каким-нибудь текстовым '
		'редактором .htm-файл какой-нибудь книги и посмотреть, какие теги '
		'выделяют там надписи, которые при просмотре в Цитате имеют необычное'
		' форматирование. Например для модуля "Библия (Современный перевод)" '
		'подходят опции --nt i --tt h3').decode('utf-8'))
	Parser.add_option_group(BibleModuleGroup)
	DictionaryModuleGroup=OptionGroup(Parser, ('Опции, специфичные для '
		'модулей-словарей').decode('utf-8'))
	DictionaryModuleGroup.add_option('--dt','--dictionarytype',\
		dest='DictionaryType', default='Generic', help=(\
		'тип словаря. Допустимые значения: '
		'HebrewStrong, GreekStrong, Generic (по умолчанию). GreekStrong для '
		'греческого словаря Стронга, HebrewStrong для еврейского.').\
		decode('utf-8'), choices=['HebrewStrong', 'GreekStrong', 'Generic'],\
		type='choice')
	Parser.add_option_group(DictionaryModuleGroup)
	(Options, args) = Parser.parse_args()
	#проверяем, указал ли пользователь входной файл
	if len(args) == 1:
		print ('Путь до входного файла введен').decode('utf-8')
		Options.InputFileName = args[0]
	else:
		print ('Ошибка! Не введен путь до входного файла.').decode('utf-8')
		print ('Для файлов библейских модулей это bibleqt.ini.').decode('utf-8')
		print ('Для словарей это .htm-файл со словарем.').decode('utf-8')
		print ('Вызовите скрипт с параметром -h для просмотра опций').\
			decode('utf-8')
		print ('Введите: '+sys.argv[0]+' -h').decode('utf-8')
		sys.exit(1) #завершаем работу скрипта
	# запускаем процесс преобразования
	Converter=CConverter(Options)
	del Options
	Converter.MakeConversion()

