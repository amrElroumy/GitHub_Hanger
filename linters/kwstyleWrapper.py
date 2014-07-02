#!/usr/bin/env python
import sys
import os
import glob
import subprocess
import re
import configobj

ignoreList = []
filesPatternsToLint = []

def accumulateFileNames(resultList, currentDir, filesInCurrentDir):
    currentDir = os.path.normpath(os.path.normcase(currentDir)) + os.path.sep

    #see if I need to ignore this whole directory
    for ignoreEntry in ignoreList:
        if(re.search(ignoreEntry, currentDir)):
            return

    #for each file in the current directory
    for fileName in filesInCurrentDir:
        ignoreIt = False
        for ignoreEntry in ignoreList: #see if it should be ignored
            if re.search(ignoreEntry, fileName):
                ignoreIt = True
                break
        if (not ignoreIt): #if it's not explicitly ignored
            for pattern in filesPatternsToLint:
                if re.search(pattern, fileName): #if it matches one of the patterns for the files I want to lint
                    resultList.append(currentDir + fileName)


#takes the output of kwstyle for a single file and parses it into a list of tuples
#each tuple has 3 elements: (filename, line number, warning string)
def splitFileWarnings(rawTextBlob):
    #warning format is
    #       filename(linenumber) : warning
    #       possibly multiple lines for the warning

    #split the text into lines
    rawLines = rawTextBlob.splitlines()

    #find all lines that begin a warning
    pattern = r"^(.+?\(\d+\)\s*:)"
    warningHeaders = re.findall(pattern, rawTextBlob, re.MULTILINE)

    #find the indices of the lines that begin warnings
    startingIndices = []
    for header in warningHeaders:
        for i in range(len(rawLines)):
            if(header in rawLines[i]):
                startingIndices.append(i)
                break

    #re-arrange the errors/warnings into a list of errors/warnings, each warning/error is a string
    semirawList = []
    for i in range(len(startingIndices) - 1):
        start = startingIndices[i]
        end = startingIndices[i+1]
        temparray = ""
        j = start
        while j < end:
            temparray += "\n" + rawLines[j]
            j+=1
        semirawList.append(temparray)

    #handle last element in starting indices if it's not empty
    if len(startingIndices) > 0:
        temparray = ""
        start = startingIndices[-1]
        while start < len(rawLines):
            temparray += "\n" + rawLines[start]
            start+=1
        semirawList.append(temparray)

    #transform each error into a 3 tuple (filename, line number, warning/error string)
    result = []
    for str in semirawList:
        matchRes = re.search(r"^(.+?)\((\d+)\)\s*:((?:.*\n?)*)", str, flags=re.MULTILINE)
        if(matchRes):
            result.append(matchRes.groups())

    return result


def lint(configObj, pathToLint):
    if not(os.path.exists(pathToLint) and os.path.isdir(pathToLint)):
        raise Exception("Path to lint doesn't exist or not a directory")

    #Process input configuration
    pathToLint = os.path.normpath(os.path.normcase(pathToLint)) + os.path.sep
    xmlConfigFile = configObj["KWStyle"]["xml_config_file"]

    for pattern in configObj["ignore_patterns"]:
        ignoreList.append(pattern)

    try: #there might be nested patterns specific to me
        for pattern in configObj["KWStyle"]["ignore_patterns"]:
            ignoreList.append(pattern)
    except Exception:
        pass

    for pattern in configObj["include_patterns"]:
        filesPatternsToLint.append(pattern)

    try: #there might be nested patterns specific to me
        for pattern in configObj["KWStyle"]["include_patterns"]:
            ignoreList.append(pattern)
    except Exception:
        pass

    filenames = []
    os.path.walk(pathToLint, accumulateFileNames, filenames)#recurses on the directories rooted at "pathToLint" accumulating "filenames" to lint them

    result = []
    for file in filenames:
        command = "KWStyle '" + file + "' -msvc -xml '" + xmlConfigFile + "'"
        try:
            runRes = subprocess.check_output([command], shell=True)
        except subprocess.CalledProcessError as e:
            runRes = e.output #KWStyle returns exit code 1 to indicate errors/warnings, so check_output(...) throws an exception

        if len(runRes) > 0:
            result.extend(splitFileWarnings(runRes))

    return result

