import sublime, sublime_plugin
import tokenize
#from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP
import sys, os

class PreSaveFormatListner(sublime_plugin.EventListener):
    """Event listener to run CssFormat during the presave event"""
    def on_pre_save(self, view):
        fName = view.file_name()
        vSettings = view.settings()
        syntaxPath = vSettings.get('syntax')
        syntax = ""
        ext = ""

        if (fName != None): # file exists, pull syntax type from extension
            ext = os.path.splitext(fName)[1][1:]
        if (syntaxPath != None):
            syntax = os.path.splitext(syntaxPath)[0].split('/')[-1].lower()

        formatFile = ext in ['css'] or "css" in syntax

        if (formatFile):
            view.run_command("cssformat")

class CssformatCommand(sublime_plugin.TextCommand):
    finalText = ""
    line = ""

    def run(self, edit):
        finalText = ""
        line = ""

        curr_view = self.view

        result = []
        indentedLines = []
        flatLines = []
        spacedLines = []
        multilineText = []

        def getTheLines():
            for x in curr_view.substr(sublime.Region(0, curr_view.size())).split("\n"):
                result.append(x)
            if len(result[-1].strip()) == 0:
                result.pop()

        def flattenTheText():
            counter = 0
            while counter < len(indentedLines):
                self.line = indentedLines[counter]

                #remove all strange characters from the begining of the line
                while self.line[0] > '~':
                    self.line = self.line[1:len(self.line)]

                #remove spaces and tabs from the end of the line
                while self.line.endswith(' ') or self.line.endswith('\t'):
                    self.line = self.line[0:len(self.line)-1]

                #look for opening curly braces
                if not self.line.startswith('@'):
                    if self.line.endswith('{') or (('{' in self.line) and ('}' not in self.line) and not self.line.startswith('/*')):
                        while self.line.endswith('\n'):
                            self.line = self.line[0:len(self.line)-1]
                        counter += 1
                        nextLine = indentedLines[counter]
                        while nextLine.startswith('\t') or nextLine.startswith(' '):
                            nextLine = nextLine[1:len(nextLine)]
                        while nextLine.endswith('\n') or nextLine.endswith('\r') or nextLine.endswith('\r\n'):
                            nextLine = nextLine[0:len(nextLine) - 1]
                        
                        #check for commented lines
                        if nextLine.startswith("/*") and (nextLine.endswith("*/") or nextLine.endswith("*/ ") or nextLine.endswith("*/  ")):
                            try:
                                ind = nextLine.index(';')
                            except Exception, e:
                                ind = -1
                            while ind > -1:
                                nextLine = nextLine[0:ind] + nextLine[ind + 1:len(nextLine)]
                                try:
                                    ind = nextLine.index(';')
                                except Exception, e:
                                    ind = -1
                            self.line += '$' + nextLine + ';'
                        else:
                            if nextLine.endswith('*/'):
                                try:
                                    ind = nextLine.index(';')
                                except Exception, e:
                                    ind = -1
                                
                                if ind > -1 and len(nextLine) > (ind + 1):
                                    while nextLine[ind - 1] == ' ':
                                        nextLine = nextLine[0:ind - 1] + nextLine[ind:len(nextLine)]
                                        try:
                                            ind = nextLine.index(';')
                                        except Exception, e:
                                            ind = -1
                                    nextLine = nextLine[0:ind] + nextLine[ind + 1:len(nextLine)]
                                self.line += nextLine + ";"
                            else:
                                self.line += nextLine

                        
                        while (not self.line.endswith('}')) and len(indentedLines) > counter + 1:
                            counter += 1
                            nextLine = indentedLines[counter]
                            while nextLine.startswith('\t') or nextLine.startswith(' '):
                                nextLine = nextLine[1:len(nextLine)]
                            while nextLine.endswith('\n') or nextLine.endswith('\r') or nextLine.endswith('\r\n'):
                                nextLine = nextLine[0:len(nextLine) - 1]
                            #check for commented lines
                            if nextLine.startswith("/*") and (nextLine.endswith("*/") or nextLine.endswith("*/ ") or nextLine.endswith("*/  ")):
                                try:
                                    ind = nextLine.index(';')
                                except Exception, e:
                                    ind = -1
                                while ind > -1:
                                    nextLine = nextLine[0:ind] + nextLine[ind + 1:len(nextLine)]
                                    try:
                                        ind = nextLine.index(';')
                                    except Exception, e:
                                        ind = -1
                                self.line += '$' + nextLine + ';'
                            else:
                                if nextLine.endswith('*/'):
                                    try:
                                        ind = nextLine.index(';')
                                    except Exception, e:
                                        ind = -1
                                    if ind > -1 and len(nextLine) > (ind + 1):
                                        while nextLine[ind - 1] == ' ':
                                            nextLine = nextLine[0:ind - 1] + nextLine[ind:len(nextLine)]
                                            try:
                                                ind = nextLine.index(';')
                                            except Exception, e:
                                                ind = -1
                                        nextLine = nextLine[0:ind] + nextLine[ind + 1:len(nextLine)]
                                    self.line += nextLine + ";"
                                else:
                                    if not nextLine.startswith("/*"):
                                        self.line += nextLine                                

                        #Let's not forget the last line
                        # this is for only special case, when closing curly brace is on the same line as
                        #  the last commented line
                        # print 'last line is: ', nextLine
                        if nextLine.startswith("/*"):
                            try:
                                ind = nextLine.index(';')
                            except Exception, e:
                                ind = -1
                            while ind > -1:
                                nextLine = nextLine[0:ind] + nextLine[ind + 1:len(nextLine)]
                                try:
                                    ind = nextLine.index(';')
                                except Exception, e:
                                    ind = -1
                            self.line += '$' + nextLine[0:len(nextLine) - 1] + '; }'
                
                while self.line.endswith('\n') or self.line.endswith('\r') or self.line.endswith('\r\n') or self.line.endswith(' '):
                    self.line = self.line[0:len(self.line)-1]           
                
                flatLines.append(self.line + '\n')
                counter += 1

        def fixIndentations():
            counter = 0;
            while counter < len(result):
                line = result[counter]
                #remove spaces and tabs from the end of the line
                while line.endswith(' ') or line.endswith('\t'):
                    line = line[0:len(line)-1]
                #check if the line is indented
                if line.startswith(' ') or line.startswith('\t'):
                    count = 0
                    spCount = 0
                    tabCount = 0

                    while line.startswith(' ') or line.startswith('\t'):
                        count += 1
                        if line.startswith(' '):
                            spCount += 1
                        if line.startswith('\t'):
                            tabCount += 1
                        line = line[1:len(line)]
                    spaceCount = (spCount / 4) + tabCount

                    #replace the spaces with tabs
                    tabs = ""
                    x = 0
                    while x < spaceCount:
                        tabs += '\t'
                        x += 1
                    line = tabs + line

                indentedLines.append(line + '\n')
                counter += 1

        def addSpaces():
            counter = 0
            while counter < len(flatLines):
                line = flatLines[counter]
                charCounter = 0
                while charCounter < len(line):
                    #add spaces before curly braces
                    if charCounter > 0:
                        if (line[charCounter] == '{' or line[charCounter] == '}') and line[charCounter-1] != ' ':
                            line = line[0:charCounter] + ' ' + line[charCounter:len(line)]
                            charCounter += 1
                    
                    charCounter += 1
                counter += 1
                spacedLines.append(line)

        def sortThis(listToSort):
            newList = []
            for param in listToSort:
                while param.startswith(' '):
                    param = param[1:len(param)]
                try:
                    colonIndex = param.index(':')
                except Exception, e:
                    colonIndex = -1
                if colonIndex > -1:
                    param = param[0:colonIndex] + ' ' + param[colonIndex + 1:len(param)]
                newList.append(param + ';')

            #sort the list
            newList.sort()

            # manage the special characters
            arraySize = len(newList)
            x = 0
            while x < arraySize:
                line = newList[x]
                #start with placing colons back in
                try:
                    spaceIndex = line.index(' ')
                except Exception, e:
                    spaceIndex = -1
                if spaceIndex > -1 and (not line.startswith('$')):
                    line = line[0:spaceIndex] + ':' + line[spaceIndex :len(line)]
                # removing extra spaces
                while line.startswith(' '):
                    line = line[1:len(line)]

                #reset the value
                newList[x] = line

                if line.startswith('*') or line.startswith('_'):
                    newList.remove(line)
                    newList.append(line)
                    x -= 1
                    arraySize -= 1

                if line.startswith('-'):
                    newList.remove(line)
                    newList.insert(0, line)

                x += 1

            # manage the comments
            arraySize = len(newList)
            x = 0
            while x < arraySize:
                line = newList[x]
                if line.startswith('$'):
                    newList.remove(line)
                    newList.append(line[1:len(line) - 1])
                    x -= 1
                    arraySize -= 1
                x += 1
            # More magic is needed here
            arraySize = len(newList)
            x = 0
            while x < arraySize:
                line = newList[x]
                try:
                    colonIndex = line.index(":  ")
                except Exception, e:
                    colonIndex = -1
                while colonIndex > -1 and (len(line) > (colonIndex + 2)):
                    line = line[0:colonIndex + 1] + line[colonIndex + 2: len(line)]
                    try:
                        colonIndex = line.index(":  ")
                    except Exception, e:
                        colonIndex = -1
                newList[x] = line
                x += 1

            return newList


        def toMultipleLines():
            counter = 0
            nextText = ""
            inMediaSection = False
            while counter < len(spacedLines):
                line = spacedLines[counter]

                # now, check if the line contains multiple parameters
                try:
                    openIndex = line.index('{')
                except Exception, e:
                    openIndex = -1
                try:
                    closeIndex = line.index('}')
                except Exception, e:
                    closeIndex = -1

                if (not line.startswith('/*')) and openIndex > -1 and (closeIndex - openIndex) > 5:
                    declaration = line[0:openIndex + 1] + '\n'
                    # check if the line is inside a media section
                    if inMediaSection:
                        declaration = '\t' + declaration

                    # remove the last semicolon
                    newLine = line[openIndex + 1:closeIndex]
                    while newLine.endswith(' '):
                        newLine = newLine[0:len(newLine) - 1]

                    displayLine = ""
                    paramCounter = 0
                    mainCounter = 0
                    startCounter = 0
                    listOfParams = []
                    while mainCounter < len(newLine):
                        if newLine[mainCounter] == ';':
                            # print 'Param ',paramCounter,' is: ', newLine[startCounter:mainCounter]
                            # print '-Starting char is: ',newLine[startCounter]
                            listOfParams.append(newLine[startCounter:mainCounter])
                            mainCounter += 1
                            startCounter = mainCounter
                            paramCounter += 1

                        mainCounter += 1


                    # Now, sort the list
                    listOfParams = sortThis(listOfParams)

                    # get line's indentations
                    tabCount = 0
                    tabs = ""
                    while declaration[tabCount] == '\t':
                        tabCount += 1
                        tabs += '\t'

                    for param in listOfParams:
                        # fix lines with comments at the end
                        if param.endswith("*/;") and (not param.startswith("/*")):
                            # print 'found a param that ends with a comment **************'
                            
                            #let's start by removing the ending semicolon
                            param = param[0:len(param)-1]
                            try:
                                startIndex = param.index("/*")
                            except Exception, e:
                                startIndex = -1

                            # first, remove extra spaces
                            while param[startIndex - 1] == ' ':
                                param = param[0:startIndex - 1] + param[startIndex:len(param)]
                                try:
                                    startIndex = param.index("/*")
                                except Exception, e:
                                    startIndex = -1

                            # place semicolon back in
                            param = param[0:startIndex] + '; ' + param[startIndex:len(param)]

                        displayLine += tabs + '\t' + param + '\n'

                    multilineText.append(declaration + displayLine + tabs + '}\n')

                else:
                    # check for lines starting with @
                    if line.startswith('}'):
                        inMediaSection = False

                    if inMediaSection:
                        line = '\t' + line
                        multilineText.append(line)
                    else:
                        multilineText.append(line)

                    if line.startswith('@'):
                        inMediaSection = True
                    

                counter += 1

        getTheLines()
        fixIndentations()
        flattenTheText()
        addSpaces()
        toMultipleLines()

        self.view.sel().clear()
        fileSize = self.view.size()

        self.view.erase(edit, sublime.Region(0, fileSize + 200))
        
        numLines = len(multilineText) - 1
        while numLines > -1:
            self.view.insert(edit, 0, multilineText[numLines])
            numLines -= 1
