# This file is part of saddle-bags.
#
# saddle-bags is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# saddle-bags is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Publsic License
# along with saddle-bags. If not, see <http://www.gnu.org/licenses/>.

import sys
from sys import exc_info

from datetime import datetime

import csv

try:
    from sys import _MEIPASS
except Exception:
    print('No MEIPASS Directory. This is not running from a compiled EXE file. No problem.')

from os import makedirs, remove, rmdir, name
from os.path import join, expanduser, isfile, abspath, isdir, split

from tkinter import messagebox, simpledialog

from xml.etree import ElementTree as ET
from xml.dom import minidom as MD

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna

from io import StringIO
from json import loads, dumps # these method names are terrible IMO.

from zipfile import ZipFile

from saddlebags.AlleleSubmission import HlaGene, GeneFeature, SubmissionBatch, AlleleSubmission
from saddlebags.IpdSubGenerator import IpdSubGenerator # TODO: I shouldn't need to import this one. I'm making circular dependencies.
# TODO: Fix this, i think the solution is moving stuff from this file to IPDSubGenerator. Or GoogleDriveUpload.

import logging

from gfe_client import Configuration, ApiClient, TypeSeqApi

def showInfoBox(title, message):
    # A wrapper method for the tkinter popup box.
    messagebox.showinfo(title, message)

def getInfoBox(title, message):
    # wrapper to get a text input from the user.
    return simpledialog.askstring(title, message)

def showYesNoBox(title, message):
    # A wrapper method for the tkinter ask yes/no question box.
    response = messagebox.askquestion(title, message,icon='warning')
    # the response is a string, 'yes' or 'no'. That's really funny.
    return response == 'yes'

def fetchSequenceAlleleCallWithGFE(rawSequence, locus):
    logging.debug('Attempting to fetch an allele call using GFE.')
    logging.debug(rawSequence)
    logging.debug(locus)

    cleanedSequence = cleanSequence(rawSequence.upper())

    # TODO: get the act address into a configuration file. I want to be able to use a local service. Which i already have?
    config = Configuration()
    config.host = 'http://act.b12x.org'

    # Set the log file for seeing urllib and gfe logging.
    # https://github.com/nmdp-bioinformatics/gfe_client
    logFileLocation = join(getSaddlebagsDirectory(),'Saddlebags.GFE.Log.txt')
    # In Configuration.py Mike made his "setters" in a cool pythony way.
    # It was sorta confusing but I can just assign it like a normal parameter.
    config.logger_file = logFileLocation
    # debug is like "verbose", the log is empty when debug is disabled.
    config.debug = True

    proxy = getConfigurationValue('proxy')
    if(proxy == None or proxy == 'None' or proxy == ''):
        config.proxy = None
    else:
        config.proxy = proxy
    logging.warning('Assigning this proxy value: ' + str(config.proxy))
    # TODO: this proxy code is completely untested. Johnny can help me with that?

    #Set up the API.
    api = ApiClient(configuration=config)
    ann_api = TypeSeqApi(api_client=api)

    responseText = ann_api.typeseq_get(sequence=cleanedSequence, imgthla_version="3.31.0", locus='HLA-A')

    annotation = responseText.to_dict()
    jsonResponse = dumps(annotation, indent=4)

    logging.debug('Response:\n' + jsonResponse)
    return jsonResponse


def assignIcon(tkRootWindow):
    logging.debug ('Assigning Icon for the GUI.')

    # Find window location inside executable
    try:
        # Changing this to use the join function, I don't know why I did this double slash thing before.
        # TODO: Does the icon work in the compiled exe?
        #iconFileLocation = resourcePath('images\\horse_image_icon.ico')
        windowsIconFileLocation = resourcePath(join('images', 'horse_image_icon.ico'))
        linuxIconFileLocation = resourcePath(join('images', 'horse_image_icon.xbm'))



        # Different icon code for Linux and Windows. "name"="os.name"
        if "nt" == name:
            logging.debug('I am assigning this icon:' + windowsIconFileLocation)
            tkRootWindow.wm_iconbitmap(bitmap=windowsIconFileLocation)
        else:
            logging.debug('I am assigning this icon:@' + linuxIconFileLocation)
            tkRootWindow.wm_iconbitmap(bitmap="@" + linuxIconFileLocation)
    except Exception:
        #base_path = os.path.abspath(".")
        logging.error('Could not assign icon based on path inside executable.')
        
        logging.error (exc_info())

    # Linux
    # I have given up on setting an icon in linux. I can't seem to load up any file format.
  
 
def resourcePath(relativePath):
    # Where will I find my resources? This should work in, or outside, a compiled EXE
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return join(_MEIPASS, relativePath)
    return join(abspath('.'), relativePath)

# This is a short wrapper method to use biopython's translation method. 
# Most of this code is just checking for things that went wrong

def translateSequence(submission):

    inputSequence = submission.submittedGene.getExonSequence()
    proteinSequence = ''
    
    try:
        # Do nothing if the input sequence is blank.
        if( len(inputSequence) > 0 ):
            
            coding_dna = Seq(inputSequence, generic_dna)        
            proteinSequence = str(coding_dna.translate())   
            logging.debug ('Exon Sequence before translation:' + coding_dna)
            logging.debug ('Translated Protein:' + proteinSequence)
            
            # Perform Sanity Checks.
            # Stop codon *should* be at the end of the protein.  
            # Here we seek out the first instance of a stop codon, 
            # and remove the peptides afterwards.
            # because that's what happens in real life.
            stopCodonLocation = proteinSequence.find('*')
            
            # If no stop codon was found
            if (stopCodonLocation == -1):
                submission.isPseudoGene = True
                #assignConfigurationValue('is_pseudo_gene','1')
                logging.info ('No Stop Codon found. This is a "pseudo-gene".')
                # If multiple of three (correct codon length)
                if(len(coding_dna) % 3 == 0):
                    messagebox.showinfo('No Stop Codon Found', 
                        'The translated protein does not contain a stop codon.\n' + 
                        'This is indicated by a /pseudo flag in the sequence submission.'
                         )
                    
                # Wrong Codon Length
                else:
                    messagebox.showinfo('No Stop Codon Found', 
                        'The translated protein does not contain a stop codon.\n' + 
                        'The coding nucleotide sequence length (' + str(len(coding_dna))  + ') is not a multiple of 3.\n' + 
                        'This is indicated by a /pseudo flag in the sequence submission.')

            # If Stop Codon is in the end of the protein (This is expected and correct)
            elif (stopCodonLocation == len(proteinSequence) - 1):
                submission.isPseudoGene = False
                #assignConfigurationValue('is_pseudo_gene','0')
                
                # If multiple of three (correct codon length)
                if(len(coding_dna) % 3 == 0):
                    # Everything is fine in this case.  Trim off the stop codon
                    logging.info ('The stop codon is in the correct position. This is not a "pseudo-gene".')
                    proteinSequence = proteinSequence[0:stopCodonLocation]
                    pass 
                # Wrong Codon Length
                else:
                    logging.info ('The stop codon is in the correct position, but there are extra nucleotides. This is not a "pseudo-gene".')
                    messagebox.showinfo('Extra Nucleotides After the Stop Codon', 
                        'The stop codon is at the correct position in the protein, but ' + 
                        'The coding nucleotide sequence length (' + str(len(coding_dna))  + ') is not a multiple of 3.\n\n' +
                        'Please double check your sequence.')
                    proteinSequence = proteinSequence[0:stopCodonLocation]
                                        
            # Else Stop Codon is premature (before the end of the protein) 
            else:
                logging.info ('A premature stop codon was found. This is a "pseudo-gene".')
                submission.isPseudoGene = True
                #assignConfigurationValue('is_pseudo_gene','1')
                
                # If multiple of three (correct codon length)
                if(len(coding_dna) % 3 == 0):
                    messagebox.showinfo('Premature Stop Codon Detected',
                        'Premature stop codon found:\nProtein Position (' + 
                        str(stopCodonLocation + 1) + '/' +
                        str(len(proteinSequence)) + ')\n\n' + 
                        'This is indicated by a /pseudo flag in the sequence submission.\n' +
                        'Double check your protein sequence,\n' + 
                        'this might indicate a missense mutation.\n\n' + 
                        'Translated Protein:\n' + proteinSequence + 
                        '\n\nProtein in ENA Submission:\n' + proteinSequence[0:stopCodonLocation] +
                        '\n'
                        )
                    proteinSequence = proteinSequence[0:stopCodonLocation]


                # Wrong Codon Length
                else:
                    messagebox.showinfo('Premature Stop Codon Detected',
                        'Premature stop codon found:\nProtein Position (' + 
                        str(stopCodonLocation + 1) + '/' +
                        str(len(proteinSequence)) + ')\n\n' + 
                        'This is indicated by a /pseudo flag in the sequence submission.\n' +
                        'Nucleotide count is not a multiple of 3,\n' +
                        'Double check your protein sequence,\n' + 
                        'this might indicate a missense mutation.\n\n' + 
                        'Translated Protein:\n' + proteinSequence + 
                        '\n\nProtein in ENA Submission:\n' + proteinSequence[0:stopCodonLocation] +
                        '\n'
                        )
                    proteinSequence = proteinSequence[0:stopCodonLocation]
        else:
            logging.warning('Translating a nucleotide sequence of length 0. Done. That was easy.')
            pass

        return proteinSequence
    
    except Exception:
        logging.error ('Problem when translating protein:', 'ERROR')
        logging.error (str(exc_info()), 'ERROR')
        messagebox.showinfo('Protein Translation Error', 
            'I could not translate your protein:\n' +  str(exc_info()))
        
        raise
    
def collectAndValidateRoughSequence(guiSequenceInputObject):
    try:
        roughNucleotideSequence = collectRoughSequence(guiSequenceInputObject)
        annotatedSequence = None

        #Is this sequence in Fasta format?        
        try:
            logging.debug('Checking if sequence is fasta format.')

            fileHandleObject = StringIO(roughNucleotideSequence)
            fastaSeqList = list(SeqIO.parse(fileHandleObject, 'fasta'))
            logging.debug('The length of the fasta seq list is:' + str(len(fastaSeqList)))
            if(len(fastaSeqList) == 1):
                annotatedSequence = cleanSequence(str(fastaSeqList[0].seq))
                logging.debug ('The input sequence is in .fasta format.')
            else:
                logging.debug('This sequence is not in .fasta format.')
        except Exception:
            logging.debug('This sequence is not in .fasta format: ' + str(exc_info()))
            
        #Is this sequence in Fastq format?        
        try:
            logging.debug('Checking if sequence is fastq format.')
            fileHandleObject = StringIO(roughNucleotideSequence)
            fastqSeqList = list(SeqIO.parse(fileHandleObject, 'fastq'))
            logging.debug('The length of the fasta seq list is:' + str(len(fastaSeqList)))
            if(len(fastqSeqList) == 1):
                annotatedSequence = cleanSequence(str(fastqSeqList[0].seq))
                logging.debug ('The input sequence is in .fastq format.')
            else:
                logging.debug('This sequence is not in .fastq format.')
        except Exception:
            logging.debug('This sequence is not in .fastq format: ' + str(exc_info()))

        # TODO: If this file is xml what should we do?  Just give up i suppose.
        # TODO: I could warn the user that XML isn't supported yet...
        # We want to accept HML.  But there are too many xml formats.
        # Yeah I dunno about HML, we will not implement that right now.

        # If we haven't found an annotated sequence yet, this is not fasta or fastq.
        if(annotatedSequence is None):
            annotatedSequence = cleanSequence(roughNucleotideSequence)
        #    Rough text = all of the gui text.
            
    
        #Are we using any nonstandard / ambiguous nucleotides?
        for nucleotideCharacter in annotatedSequence:
            if(nucleotideCharacter not in ('A','G','C','T','a','g','c','t')):
                messagebox.showerror('Nonstandard Nucleotide' 
                    , 'I found a non-standard\n'
                    + 'character in your nucleotide\n'
                    + 'sequence: ' 
                    + str(nucleotideCharacter) + '\n'
                    + 'You should use standard nucleotide\n'
                    + 'characters in your submission.\n'
                    + 'I will attempt to continue.')
                break
    

    
        # TODO: Fix this last-ditch effort.
        
        #annotatedSequence = roughNucleotideSequence
        return annotatedSequence
            
    except Exception:
        #except Exception, e:
        messagebox.showerror('Error Reading Input Sequence.'
            , str(exc_info()))
        raise

def collectRoughSequence(guiSequenceInputObject):
    # This method gets the text from a gui object and returns it.
    # There is no validation performed here.
    try:
        roughNucleotideSequence = guiSequenceInputObject.get('1.0', 'end')
        return roughNucleotideSequence
            
    except Exception:
        #except Exception, e:
        messagebox.showerror('Error Reading Input Sequence.'
            , str(exc_info()))
        raise

def isSequenceAlreadyAnnotated(inputSequenceText):
    # The easy case.
    if ('a' in inputSequenceText and
        'g' in inputSequenceText and
        'c' in inputSequenceText and
        't' in inputSequenceText and
        'A' in inputSequenceText and
        'G' in inputSequenceText and
        'C' in inputSequenceText and
        'T' in inputSequenceText
        ):
        return True
    
    # TODO: This isn't perfect. It must have all 8 nucleotides to return true.
    # Circle back on this one later, should I store a variable somewhere if the sequence has been annotated?
    return False

def parseExons(roughFeatureSequence, alleleCallWithGFEJson, submission):
    
    # TODO: Parse the JSON in the alleleCallWithGFEJson.  
    # There should be some information about the exons in here.
    # ex = uppercase
    # utr/intron = lowercase
    try:

        fivePrimeSequence = ''
        threePrimeSequence = ''
        exonDictionary = {}
        intronDictionary = {}

        # The json should be a String, but it is returned from the NMDP ACT API as a "Typing" object. I convert it to a String to make everyone happy.
        jsonString = str(alleleCallWithGFEJson)
        logging.debug('THIS IS THE JSON STRING\n:' + jsonString)
        parsedJson = loads(jsonString)

        if (len(parsedJson.keys()) > 1):

            # TODO: So do I need the status or not? I Think it is necessary.
            if 'status' in parsedJson.keys():
                queryStatus = parsedJson['status']
                if(str(queryStatus) == '200'):
                    logging.debug ('Response from Allele call was status 200. That is quite normal.')
                elif(str(queryStatus) == '500'):
                    logging.error ('500 status found. Unknown server error.', 'ERROR')


                    # TODO: Is this where I can consume the error for when the ACT service is not responding properly?
                    # TODO: Yeah I think I get a 502 error when the server is overloaded. '502'.  But the response is HTML.
                    # TODO: It's not JSON so to detect that error I need to parse the XML
                    # TODO: or just search for a constant string. It could be that the response is empty, just an empty string.
                    # That's a 504 response code.

                    """
                        <html>
                        <head><title>502 Bad Gateway</title></head>
                        <body bgcolor="white">
                        <center><h1>502 Bad Gateway</h1></center>
                        <hr><center>nginx/1.15.2</center>
                        </body>
                        </html>
                        <!-- a padding to disable MSIE and Chrome friendly error page -->
                        <!-- a padding to disable MSIE and Chrome friendly error page -->
                        <!-- a padding to disable MSIE and Chrome friendly error page -->
                        <!-- a padding to disable MSIE and Chrome friendly error page -->
                        <!-- a padding to disable MSIE and Chrome friendly error page -->
                        <!-- a padding to disable MSIE and Chrome friendly error page -->
                   
                    """

                    logging.info ('JSON Results:' + str(parsedJson))
                    #messagebox.showerror('Error Annotating Sequence.',
                    #    'The ACT service returned a 500 status, there was an unknown server problem. I have no annotation results.')
                    raise Exception ('The ACT service returned a 500 status, there was an unknown server problem. I have no annotation results, you can try to annotate the sequence manually.')
                    
            else:
                logging.debug ('JSON results have no "status" element. This is not a problem.')
               
            # Is sequence novel?
            if 'status' in parsedJson.keys():
                logging.debug ('status element was found.')
            else:
                logging.error ('JSON Results:' + str(parsedJson), 'ERROR')
                raise Exception ('No status element was found in Json results. Cannot continue.')

            typingStatusNode = parsedJson['status']

            logging.debug('I will try to loop through the keys of the typing status dictionary.')
            logging.debug('the typing status dictionary looks like this:')
            logging.debug(typingStatusNode)
            
            if(typingStatusNode == 'documented'):
                logging.info ('This is a known/documented allele.')
            elif(typingStatusNode == 'novel'):
                logging.info ('This is a novel allele.')
            elif(typingStatusNode == 'novel_combination'):
                logging.info ('This is a novel combination of gene features.')
            else:
                logging.error('I do not understand the status of this allele. Expected either "documented" or "novel" or "novel_combination":','ERROR')
                logging.error(typingStatusNode,'ERROR')
                raise Exception('Unknown Typing status, expected documented or novel:' + typingStatusNode)

            # TODO: This format is different. Re-work this logic until it is better.

            # Loop through the recognized Features
            if 'features' in parsedJson.keys():
                # We found features.
                featureList = parsedJson['features']
                logging.info ('I found this many Known Features:' + str(len(featureList)))
                
                for featureDictionary in featureList:
                    
                    term=str(featureDictionary['term'])
                    rank=str(featureDictionary['rank'])
                    sequence= str(featureDictionary['sequence'])
                    
                    logging.debug('Known Feature'
                        + ':' + term
                        + ':' + rank
                        + ':' + sequence)
                    
                    if(term == 'five_prime_UTR'):
                        fivePrimeSequence = sequence.lower()
                    elif(term == 'three_prime_UTR'):
                        threePrimeSequence = sequence.lower()
                    elif(term == 'exon'):    
                        exonDictionary[rank] = sequence.upper()
                    elif(term == 'intron'):    
                        intronDictionary[rank] = sequence.lower()
                    else:
                        raise Exception('Unknown Feature Term, expected exon or intron:' + term)
                
                logging.debug('fivePrimeSequence:\n' + str(fivePrimeSequence))
                logging.debug('threePrimeSequence:\n' + str(threePrimeSequence))
                logging.debug('exonCount:\n' + str(len(exonDictionary.keys())))
                logging.debug('intronCount:\n' + str(len(intronDictionary.keys())))
            else:
                raise Exception ('Unable to identify any HLA exon features, unable to annotate sequence.')
                # no features found
                #return roughFeatureSequence

            # TODO: Once we know the genomic features, I can add this next-closest allele description.

            alleleDescription = ''
            if 'hla' in parsedJson.keys():
                closestAllele = parsedJson['hla']
                alleleDescription += (closestAllele)

                # if seqdiff is available, parse that list and specify the allele differences.
                # This has the most info but its missing from old versions of ACT.
                # else if novel_features are available, at least I can tell what feature the modification is in.
                # else, assume the sequence is known, not novel.
                if 'seqdiff' in parsedJson.keys():
                    seqDiffList = parsedJson['seqdiff']

                    # seqDiffList can be None, if there are no known sequence differences.
                    if(seqDiffList is not None):
                        for seqDiffDictionary in seqDiffList:

                            alleleDescription += ('\nFT                  Position '
                                + str(seqDiffDictionary['location']) + ' in '
                                + str(seqDiffDictionary['term']) + ' : '
                                + str(seqDiffDictionary['ref']) + '->' + str(seqDiffDictionary['inseq'])
                                )
                    else:
                        logging.info('No unknown features. This allele is documented. Cool.')



                # Loop Novel Features
                elif 'novel_features' in parsedJson.keys():
                    novelFeatureList = parsedJson['novel_features']

                    # In this case I only have info about the feature it is in. Darn.
                    # TODO Make this a bit more descriptive
                    for featureDictionary in novelFeatureList:
                        alleleDescription += ('\nNovel '
                            + str(featureDictionary['term']) + ' ' + str(featureDictionary['rank']))


                else:
                    # Add the Sequence Differences.
                    alleleDescription += ('No novel features identified. This sequence is not novel?')

            else:
                alleleDescription += 'Could not determine closest HLA allele, please provide a detailed description of the novel sequence.'

            #assignConfigurationValue('closest_allele_written_description', alleleDescription)
            submission.closestAlleleWrittenDescription = alleleDescription

            if (len(fivePrimeSequence) < 1):
                logging.warning ('I cannot find a five prime UTR.')
                logging.info ('Rough Sequence:\n' + cleanSequence(roughFeatureSequence).upper())
                logging.info('Annotated Sequence:\n' + cleanSequence(annotatedSequence).upper())
                raise Exception('GFE service did not find a 5\' UTR sequence. You will need to annotate the genomic features manually.')
            # What if the reported 5' UTR is less than what is returned by GFE?
            elif cleanSequence(fivePrimeSequence).upper() in cleanSequence(roughFeatureSequence).upper():
                # This means that we provided a longer sequence than what is available in the GFE service.
                #messagebox.showinfo('Short 5\' Sequence', 
                #    'The 5\' sequence from the GFE service is shorter than your provided sequence.\n'
                #    + 'I will use your sequence instead.'
                #     )
                beginIndex = cleanSequence(roughFeatureSequence).upper().find(cleanSequence(fivePrimeSequence).upper())
                endIndex = beginIndex + len(fivePrimeSequence)
                logging.info ('GFE sequence exists in rough sequence, at index: (' + str(beginIndex) + ':' + str(endIndex) + ')')
                logging.info ('previous fivePrime Sequence=\n' + fivePrimeSequence)
                fivePrimeSequence = cleanSequence(roughFeatureSequence)[0:endIndex].lower()
                logging.info ('new fivePrime Sequence=\n' + fivePrimeSequence)

            annotatedSequence = fivePrimeSequence + '\n'

            # arbitrarily choose 50.
            # TODO: this loop range is arbitrary, i'm using a for loop so i can access the index. Someone could calculate a max index.
            # Maybe indexString should just loop through the exon and intron dictionarys
            for i in range(1,50):
                indexString = str(i)
                if indexString in exonDictionary.keys():
                    logging.debug ('Annotating exon#' + indexString + ':' + str(exonDictionary[indexString]))
                    annotatedSequence += (str(exonDictionary[indexString]) + '\n')
                    
                if indexString in intronDictionary.keys():
                    logging.debug ('Annotating intron#' + indexString + ':' + str(intronDictionary[indexString]))
                    annotatedSequence += (str(intronDictionary[indexString]) + '\n')

            if (len(threePrimeSequence) < 1):
                logging.debug('Rough Sequence:\n' + cleanSequence(roughFeatureSequence).upper())
                logging.debug('Annotated Sequence:\n' + cleanSequence(annotatedSequence).upper())

                #raise Exception('GFE service did not find a 3\' UTR sequence. You will need to annotate the genomic features manually.')
                logging.warning('There is no three prime sequence.')
                
                # if sequence so far is in the rough sequence
                if cleanSequence(annotatedSequence).upper() in cleanSequence(roughFeatureSequence).upper():
                    # use rest of the sequence as the UTR.
                    beginIndex = cleanSequence(roughFeatureSequence).upper().find(cleanSequence(annotatedSequence).upper()) + len(cleanSequence(annotatedSequence))
                    #endIndex = len(roughFeatureSequence)
                    threePrimeSequence = cleanSequence(roughFeatureSequence)[beginIndex:].lower()
                    logging.info('Using the rest of the sequence as the 3\' UTR:\n' + threePrimeSequence)
                    annotatedSequence += threePrimeSequence
                
                
            else:
            
                annotatedSequence += threePrimeSequence
            
            # TODO: I need to have better checks here.  What is missing?
            # Do the annotated sequence and rough sequence match?
            if(cleanSequence(annotatedSequence).upper() == cleanSequence(roughFeatureSequence).upper()):
            
                return annotatedSequence
            
            else:
                logging.info ('Rough Sequence:\n' + cleanSequence(roughFeatureSequence).upper())
                logging.info ('Annotated Sequence:\n' + cleanSequence(annotatedSequence).upper())

                raise Exception('Annotated sequence and rough sequence do not match.')
        
    
            
        else:
            raise Exception ('No keys found in the JSON Dictionary, unable to annotate sequence.')
            # no keys in JSON dictionary.
            #return roughFeatureSequence

    
        raise Exception ('Reached end of parsing without returning a value.')
    
    
    except Exception:
        logging.error ('Exception when parsing exons:', 'ERROR')
        logging.error (str((exc_info())),'ERROR')
        messagebox.showinfo('Exon Parsing Error', 
            'I had trouble annotating your sequence:\n' 
            +  str(str(exc_info()) 
            + '. You will have to annotate manually.'))
        return roughFeatureSequence
        
        #raise

def cleanSequence(inputSequenceText):
    # Trim out any spaces, tabs, newlines. 
    cleanedSequence = inputSequenceText.replace(' ','').replace('\n','').replace('\t','').replace('\r','')
    return cleanedSequence

# The input file should be a string of nucleotides, with capital letters to identify exons and introns.
# Annotations are expected and read in this format:
# fiveprimeutrEXONONEintrononeEXONTWOintrontwoEXONTHREEthreeprimeutr
# agctagctagctAGCTAGCtagctagctAGCTAGCtagctagctAGCTAGCTAgctagctagctag
# All spaces, line feeds, and tabs are removed and ignored.  
def identifyGenomicFeatures(inputSequenceText):

    logging.info('Identifying Genomic Features....')
    # TODO: I should accept a Fasta Input.
    # Disregard the header line completely. Is there still sequence?
    resultGeneLoci = HlaGene()
    
    cleanedGene = cleanSequence(inputSequenceText)
    
    # Capitalize, so I can store a copy of the full unannotated sequence.
    unannotatedGene = cleanedGene.upper()
    resultGeneLoci.fullSequence = unannotatedGene
    logging.info('Total Sequence Length = ' + str(len(unannotatedGene)))

    # Loop through the cleaned and annotated input sequence, 
    # capitals and lowercase letters to determine exon start and end
    if(len(cleanedGene) > 0):
        
        # Is the first feature an exon or an intron?
        # If we begin in an Exon
        if( cleanedGene[0] in ('A','G','C','T')):                
            insideAnExon = True
        # If we begin in an Intron/UTR
        elif( cleanedGene[0] in ('a','g','c','t')):  
            insideAnExon = False
        else:
            # Nonstandard nucleotide? I should start panicking.
            #raise Exception('Nonstandard Nucleotide, not sure how to handle it')
            logging.error('Nonstandard Nucleotide at the beginning of the sequence, not sure how to handle it', 'ERROR')
            insideAnExon = False
        
        
        locusBeginPosition = 0
        for x in range(0, len(cleanedGene)):
            currentChar = cleanedGene[x]
            
            # Is this a standard nucleotide character?
            if(currentChar.upper() in ('A','G','C','T')):

                if(currentChar.isupper()):
                    if(insideAnExon):
                        #We're STILL in an exon.  In this case, I should just do nothing and continue.  
                        pass
                    else:
                        #In this case, we're just starting an EXON.
                        #Store the last Intron in the list.
                        currentIntron = GeneFeature()
                        currentIntron.sequence = cleanedGene[locusBeginPosition:x].upper()
                        currentIntron.exon = False
                        resultGeneLoci.features.append(currentIntron)
                        insideAnExon=True
                        locusBeginPosition = x
                        pass
                        
                else:
                    if not (insideAnExon):
                        #We're STILL in an intron.  Continue.
                        pass
                    else:
                        #Starting a new Intron.
                        # Store an Exon in the list.
                        currentExon = GeneFeature()
                        currentExon.sequence = cleanedGene[locusBeginPosition:x].upper()
                        currentExon.exon = True
                        resultGeneLoci.features.append(currentExon)
                        insideAnExon = False
                        locusBeginPosition=x
                        pass
            else:
                logging.warning('Nonstandard nucleotide detected at position ' + str(x) + ' : ' + currentChar
                    + '.  If this is a wildcard character, you might be ok.')

        # We've reached the end of the loop and we still need to store the last feature.
        # Should be a 3' UTR, but I can't be sure, people like to put in weird sequences.
        currentIntron = GeneFeature()
        currentIntron.sequence = cleanedGene[locusBeginPosition:len(cleanedGene)].upper()
        currentIntron.exon = insideAnExon
        resultGeneLoci.features.append(currentIntron)

        # Annotate the features (name them) and print the results of the read file.
        resultGeneLoci.annotateFeatures()
        #resultGeneLoci.printGeneSummary()
    
    # If the sequence is empty
    else:
        logging.warning('Empty sequence during gene annotation, I don\'t have anything to do.')
        
    return resultGeneLoci    
    #self.sequenceAnnotation = resultGeneLoci

# This method is a directory-safe way to open up a write file.
def createOutputFile(outputfileName):
    tempDir, tempFilename = split(outputfileName)
    if not isdir(tempDir):
        logging.info('Making Directory for output file:' + tempDir)
        makedirs(tempDir)
    resultsOutput = open(outputfileName, 'w')
    return resultsOutput

# Clear my configuration, fearlessly and without hesitation.
def clearGlobalVariables():
    global globalVariables
    globalVariables = {}

# I'm storing global variables in a dictionary for now. 
def initializeGlobalVariables():    
    global globalVariables 
    
    if not ("globalVariables" in globals()):
        globalVariables={}

        submissionBatch = SubmissionBatch()
        assignConfigurationValue('submission_batch', submissionBatch) # Potential infinite recursion, careful with this one.
        
def assignConfigurationValue(configurationKey, configurationValue):
    # assignConfigurationValue will overwrite config value without question.
    initializeGlobalVariables()

    # Lists or Strings are handled well by the configuration serializer.
    if(type(configurationValue) is list or type(configurationValue) is str ):
        globalVariables[configurationKey] = serializeConfigValue(configurationValue)
    else:
        globalVariables[configurationKey] = configurationValue

    globalVariables[configurationKey] = configurationValue
    logging.debug ('Just stored configuration key ' + configurationKey + ' which is ' + str(configurationValue) + ' of type ' + str(type(configurationValue)))

def assignIfNotExists(configurationKey, configurationValue):
    # Use this assigner if we want to declare important, new configuration values.
    # Using this method, we will not overwrite custom values
    # But we will provide critical new config values.
    initializeGlobalVariables()
    if configurationKey not in globalVariables.keys():
        assignConfigurationValue(configurationKey, configurationValue)

def getConfigurationValue(configurationKey):
    if configurationKey in globalVariables.keys():

        configurationValue = globalVariables[configurationKey]

        logging.debug ('Retrieving configuration key ' + configurationKey + ' which is ' + str(configurationValue) + ' of type ' + str(type(configurationValue)))

        if (type(configurationValue) is str):
            return deserializeConfigValue(configurationValue)
        else:
            return configurationValue
    else:
        logging.warning ('Configuration Key Not Found:' + configurationKey)
        #raise KeyError('Key Not Found:' + configurationKey)
        return None

def initializeLog():
    logFileLocation = join(getSaddlebagsDirectory(),'Saddlebags.Log.txt')

    # If there is no "globals" yet, then I haven't loaded a config yet, lets default to 'DEBUG' level.
    if (not ("globalVariables" in globals()) or  getConfigurationValue('logging') is None):
        logLevelText = 'DEBUG'
    else:
        logLevelText = getConfigurationValue('logging')

    logLevel = getattr(logging,logLevelText.upper())

    logFormatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
    rootLogger = logging.getLogger()

    # Remove handlers, It's easiest for me to add my own.
    rootLogger.handlers = []
    rootLogger.setLevel(logLevel)

    # Add the Stream Handler to print to console.
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    # Add the File Handler to log to a file.
    fileHandler = logging.FileHandler(logFileLocation)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)


def assignConfigName():
    # Join together the working directory, a subfolder called "saddlebags", and the config name.
    assignConfigurationValue('config_file_location',join(getSaddlebagsDirectory(),'Saddlebags.Config.xml'))

# Encode semicolons within a config value.
# Store lists as a string separated by a semicolon.
def serializeConfigValue(configListObject):
    #logging.debug('serializing a config value')
    if (type(configListObject) == str):
        return configListObject.replace(';','@@@')
    elif(type(configListObject) == list):
        serializedString = ''
        # TODO: what if the list elements are not strings? Just don't do that. Lol.
        # TODO: shouldn't there be built in methods for serializing? probably.
        # Encode semicolons in the list elements.
        for configString in configListObject:
            serializedString = serializedString + str(configString).replace(';','@@@') + ';'
        serializedString = serializedString[:-1]
        return serializedString
    else:
        # TODO: Yeah I did have one random problem when the type was an int. I can just always use strings or maybe handle it smarter.

        raise(Exception('Unknown configuration type, can not serialize:' + str(type(configListObject))))

# Split strings containing semicolon into a list.
# Decode @@@ back into a semicolon.
def deserializeConfigValue(serializedConfigString):
    #logging.debug('deserializing a config value')
    if (';' in serializedConfigString):
        configList = serializedConfigString.split(';')
        # Maybe a for loop is not necessary but I want to make sure i can change the string in the list.
        for i in range (0,len(configList)):
            configList[i] = configList[i].replace('@@@',';')
        return configList
    else:
        # TODO What if it's not actually a string? Could be an arbitrary object...
        return serializedConfigString.replace('@@@',';')

def writeConfigurationFile():
    assignConfigName()
    logging.debug ('Writing a config file to:\n' + getConfigurationValue('config_file_location'))

    # Root node stores "normal" configuration keys, stuff related to software
    # and not necessarily HLA or sequence submission.
    root = ET.Element("config")

    # Loop through configuration keys in the dictionary and write em out.
    for key in globalVariables.keys():
        # "normal" configuration keys, stuff related to software and not necessarily HLA or sequence submission.
        # Some config values I don't want to store. I can add more to this list if i want.
        # Don't store passwords. Passwords should be attached to the submission batch, no need to worry about it here.
        # I handle the submission batch manually.
        if(key not in [
            #'ena_password'
            #, 'ipd_password'
            #,
            'submission_batch'
            ]):

            # getConfigurationValue will handle serializing and encoding semicolons.
            ET.SubElement(root, key).text = getConfigurationValue(key)

    # Add keys for "each" batch of submissions.
    # TODO: i may add functionality for multiple batches later. Put this in a loop. Batches of Batches, I don't think this is necessary.
    submissionBatch = getConfigurationValue('submission_batch')
    
    # If the config is not already initiated, this can be None. Make a new one.
    if (submissionBatch is None):
        submissionBatch = SubmissionBatch()
    
    
    # Create a node object, most of this stuff can be parameters on the node.
    # Dont write any passwords to the config.
    submissionBatchElement = ET.SubElement(root, 'submission_batch')
    submissionBatchElement.set('enausername'      , serializeConfigValue(submissionBatch.enaUserName))
    submissionBatchElement.set('ipdsubmitterid'   , serializeConfigValue(submissionBatch.ipdSubmitterId))
    submissionBatchElement.set('ipdsubmittername' , serializeConfigValue(submissionBatch.ipdSubmitterName))
    submissionBatchElement.set('ipdaltcontact'    , serializeConfigValue(submissionBatch.ipdAltContact))
    submissionBatchElement.set('ipdsubmitteremail', serializeConfigValue(submissionBatch.ipdSubmitterEmail))
    submissionBatchElement.set('laboforigin'      , serializeConfigValue(submissionBatch.labOfOrigin))
    submissionBatchElement.set('labcontact'       , serializeConfigValue(submissionBatch.labContact))
    submissionBatchElement.set('chooseproject'    , serializeConfigValue(submissionBatch.chooseProject))
    submissionBatchElement.set('studyaccession'   , serializeConfigValue(submissionBatch.studyAccession))
    submissionBatchElement.set('projectid'        , serializeConfigValue(submissionBatch.projectId))
    submissionBatchElement.set('projectshorttitle', serializeConfigValue(submissionBatch.projectShortTitle))
    submissionBatchElement.set('projectabstract'  , serializeConfigValue(submissionBatch.projectAbstract))


    # Keys for each submission.
    for hlaSubmission in submissionBatch.submissionBatch:
        submissionElement = ET.SubElement(submissionBatchElement, 'submission')

        # Most of this stuff is attrbutes. Store the Sequence as the text of this element.
        submissionElement.text = hlaSubmission.submittedGene.getCompleteSequence()
        #print('I just assigned this fullSequence text to an XML Config element:' + submissionElement.text)
        submissionElement.set('genelocus',                       serializeConfigValue(hlaSubmission.submittedGene.geneLocus))
        submissionElement.set('localallelename'                , serializeConfigValue(hlaSubmission.localAlleleName))
        submissionElement.set('closestallelewrittendescription', serializeConfigValue(hlaSubmission.closestAlleleWrittenDescription))
        submissionElement.set('ipdsubmissionidentifier'        , serializeConfigValue(hlaSubmission.ipdSubmissionIdentifier))
        submissionElement.set('ipdsubmissionversion'           , serializeConfigValue(hlaSubmission.ipdSubmissionVersion))
        submissionElement.set('enaaccessionidentifier'         , serializeConfigValue(hlaSubmission.enaAccessionIdentifier))
        submissionElement.set('cellid', serializeConfigValue(hlaSubmission.cellId))
        submissionElement.set('ethnicorigin', serializeConfigValue(hlaSubmission.ethnicOrigin))
        submissionElement.set('sex', serializeConfigValue(hlaSubmission.sex))
        submissionElement.set('consanguineous', serializeConfigValue(hlaSubmission.consanguineous))
        submissionElement.set('homozygous', serializeConfigValue(hlaSubmission.homozygous))

        # TypedAlleles is special. It's a dictionary, where the keys are an HLA locus.
        typedAlleleText = ""
        if hlaSubmission.typedAlleles is not None:
            for loci in sorted(hlaSubmission.typedAlleles.keys()):
                typedAlleleText += str(loci) + '*' + hlaSubmission.typedAlleles[loci] + ';'
        submissionElement.set('typedalleles', serializeConfigValue(typedAlleleText))
        submissionElement.set('materialavailability', serializeConfigValue(hlaSubmission.materialAvailability))
        submissionElement.set('cellbank', serializeConfigValue(hlaSubmission.cellBank))
        submissionElement.set('primarysequencingmethodology', serializeConfigValue(hlaSubmission.primarySequencingMethodology))
        submissionElement.set('secondarysequencingmethodology', serializeConfigValue(hlaSubmission.secondarySequencingMethodology))
        submissionElement.set('primertype', serializeConfigValue(hlaSubmission.primerType))
        submissionElement.set('primers', serializeConfigValue(hlaSubmission.primers))
        submissionElement.set('sequencedinisolation', serializeConfigValue(hlaSubmission.sequencedInIsolation))
        submissionElement.set('sequencingdirection', serializeConfigValue(hlaSubmission.sequencingDirection))
        submissionElement.set('numofreactions', serializeConfigValue(hlaSubmission.numOfReactions))
        submissionElement.set('methodcomments', serializeConfigValue(hlaSubmission.methodComments))
        submissionElement.set('citations', serializeConfigValue(hlaSubmission.citations))

    xmlText = ET.tostring(root, encoding='utf8', method='xml')
    prettyXmlText = MD.parseString(xmlText).toprettyxml()
    
    xmlOutput = createOutputFile(globalVariables['config_file_location'])
    xmlOutput.write(prettyXmlText)
    xmlOutput.close()

def loadFromCSV(csvFileName):
    # Read submission data from a .csv file.
    logging.debug ('loading data from this csv file:' + csvFileName)

    # Load our submission batch. Does it already exist? It should.
    submissionBatch = getConfigurationValue('submission_batch')
    if(submissionBatch == None):
        logging.warning('Loading from CSV file. There was no batch of submissions, so I had to create an empty batch')

        submissionBatch = SubmissionBatch()

        # Assign some default information about this batch of submissions
        submissionBatch.ipdSubmitterId = ''
        submissionBatch.ipdSubmitterName = ''
        submissionBatch.ipdAltContact = ''
        submissionBatch.ipdSubmitterEmail = ''
        submissionBatch.labOfOrigin = ''
        submissionBatch.labContact = ''

    # Open the CSV and read the header.
    csvFile = open(csvFileName, 'r')
    csvInputReader = csv.reader(csvFile)

    header = next(csvInputReader)
    #logging.debug("This is the header row:" + str(header))

    # Convert the header names to uppercase to allow the input of upper or lowercase header names.
    header = [item.upper() for item in header]

    # Check for the existence of each required field in the header.
    # Store the indices of the column headers in a dictionary. So I can lookup the fields in any order, input file is more flexible.
    requiredFields = ['CLASS','CELLBANK','CELLID','CITATIONS','CLOSESTALLELEWRITTENDESCRIPTION','CONSANGUINEOUS','ETHNICORIGIN','GENELOCUS','HOMOZYGOUS','IPDSUBMISSIONIDENTIFIER','IPDSUBMISSIONVERSION','ENASEQUENCEACCESSION','LOCALALLELENAME','MATERIALAVAILABILITY','METHODCOMMENTS','NUMOFREACTIONS','PRIMARYSEQUENCINGMETHODOLOGY','PRIMERS','PRIMERTYPE','SECONDARYSEQUENCINGMETHODOLOGY','SEQUENCEDINISOLATION','SEQUENCINGDIRECTION','SEX','TYPEDALLELES','SEQUENCE']
    requiredFieldIndices = {}
    try:
        for requiredField in requiredFields:
            #print('assigning index of ' + str(requiredField) + '=' + str(header.index(requiredField)))
            requiredFieldIndices[requiredField] = header.index(requiredField)

    except:
        logging.error('Error when reading from the CSV file (' + str(csvFileName) + '). Perhaps you are missing a required field:' + str(requiredField))

    for submissionCSVRow in csvInputReader:
        #logging.debug("loading this row from csv:" + str(submissionCSVRow))


        #print ('Im creating a submission, the required field indices look like this:' + str(requiredFieldIndices))

        # Create a submission Object
        # Get each column of data and store it in the submission.
        submission = AlleleSubmission()
        # TODO: What if the .csv file is not annotated? I believe identifyGenomicFeatures expects the annotated sequence.
        submission.submittedGene = identifyGenomicFeatures( submissionCSVRow[requiredFieldIndices['SEQUENCE']])
        #submission.submittedGene.fullSequence = submissionCSVRow[requiredFieldIndices['SEQUENCE']]
        submission.submittedGene.geneLocus = submissionCSVRow[requiredFieldIndices['GENELOCUS']]
        submission.submittedGene.hlaClass = submissionCSVRow[requiredFieldIndices['CLASS']]
        submission.localAlleleName = submissionCSVRow[requiredFieldIndices['LOCALALLELENAME']]
        submission.closestAlleleWrittenDescription = submissionCSVRow[requiredFieldIndices['CLOSESTALLELEWRITTENDESCRIPTION']]
        submission.ipdSubmissionIdentifier = submissionCSVRow[requiredFieldIndices['IPDSUBMISSIONIDENTIFIER']]
        submission.ipdSubmissionVersion = submissionCSVRow[requiredFieldIndices['IPDSUBMISSIONVERSION']]
        submission.enaAccessionIdentifier = submissionCSVRow[requiredFieldIndices['ENASEQUENCEACCESSION']]
        submission.cellId = submissionCSVRow[requiredFieldIndices['CELLID']]
        submission.ethnicOrigin = submissionCSVRow[requiredFieldIndices['ETHNICORIGIN']]
        submission.sex = submissionCSVRow[requiredFieldIndices['SEX']]
        submission.consanguineous = submissionCSVRow[requiredFieldIndices['CONSANGUINEOUS']]
        submission.homozygous = submissionCSVRow[requiredFieldIndices['HOMOZYGOUS']]
        submission.typedAlleles = parseTypedAlleleInput(submissionCSVRow[requiredFieldIndices['TYPEDALLELES']])
        submission.materialAvailability = submissionCSVRow[requiredFieldIndices['MATERIALAVAILABILITY']]
        submission.cellBank = submissionCSVRow[requiredFieldIndices['CELLBANK']]
        submission.primarySequencingMethodology = submissionCSVRow[requiredFieldIndices['PRIMARYSEQUENCINGMETHODOLOGY']]
        submission.secondarySequencingMethodology = submissionCSVRow[requiredFieldIndices['SECONDARYSEQUENCINGMETHODOLOGY']]
        submission.primerType = submissionCSVRow[requiredFieldIndices['PRIMERTYPE']]
        submission.primers = submissionCSVRow[requiredFieldIndices['PRIMERS']]
        submission.sequencedInIsolation = submissionCSVRow[requiredFieldIndices['SEQUENCEDINISOLATION']]
        submission.sequencingDirection = submissionCSVRow[requiredFieldIndices['SEQUENCINGDIRECTION']]
        submission.numOfReactions = submissionCSVRow[requiredFieldIndices['NUMOFREACTIONS']]
        submission.methodComments = submissionCSVRow[requiredFieldIndices['METHODCOMMENTS']]
        submission.citations = submissionCSVRow[requiredFieldIndices['CITATIONS']]
        submissionBatch.submissionBatch.append(submission)

    csvFile.close()

def parseTypedAlleleInput(alleleInputString):
    # Typed alleles are special. It's a dictionary, where the key is the Locus (HLA-A) and the value is a String, with a list of typings separated by a comma.
    # The input is string of standard nomenclature HLA alleles, separated by a semicolon. (HLA-A*02:01;HLA-A*03:02:14)
    # submission.typedAlleles = submissionCSVRow[requiredFieldIndices['TYPEDALLELES']]
    typedAlleleDictionary = {}

    try:
        #Semicolon separates the different typing
        typedAlleleTokens = alleleInputString.split(';')
        for typedAlleleToken in typedAlleleTokens:
            # * separates the locus and allele.
            if('*' in typedAlleleToken ):
                loci, allele = typedAlleleToken.split('*')
                if loci in typedAlleleDictionary.keys():
                    typedAlleleDictionary[loci] = str(typedAlleleDictionary[loci]) + ',' + allele
                else:
                    typedAlleleDictionary[loci] = allele

        return typedAlleleDictionary
    except:
        logging.error('Error when parsing HLA typing string: ' + str(alleleInputString))
        return {}


# TODO: I suppose this method should be in an IPD SubGenerator file.
def createIPDZipFile(zipFileName):
    logging.debug('Saving Zip File:' + str(zipFileName))

    # create a temp working directory in the current folder.
    zipDirectory = getSaddlebagsDirectory()
    workingDirectory = join(zipDirectory, 'submission_temp')
    #makedirs(workingDirectory)


    # Loop through my submission batch.
    submissionBatch = getConfigurationValue('submission_batch')
    if (submissionBatch == None):
        logging.warning ('There is no submission batch, I cannot create a .zip file.')

    submissionFileList = []

    submissioncount =0
    for submissionObject in submissionBatch.submissionBatch:

        print ('Generating Submission #' + str(submissioncount))
        submissioncount += 1

        # Create a submission for each entry in the batch.

        allGen = IpdSubGenerator()
        allGen.submission = submissionObject
        allGen.submissionBatch = submissionBatch
        #allGen.sequenceAnnotation = identifyGenomicFeatures(annotatedSequence)
        ipdSubmission = allGen.buildIpdSubmission()

        submissionLocalFileName = str(submissionObject.localAlleleName) + '_submission.txt'
        submissionFileName = join(workingDirectory, submissionLocalFileName)
        submissionFileList.append(submissionLocalFileName)

        submissionFileObject = createOutputFile(submissionFileName)
        submissionFileObject.write(ipdSubmission)
        submissionFileObject.close()

        print ('I just saved this file: ' + submissionFileName)



    # create a zip file from the list of files.
    zipFileName = join(zipDirectory,zipFileName)

    with ZipFile(zipFileName,'w') as zip:
        # writing each file one by one
        for fileName in submissionFileList:
            fullPath = join(workingDirectory,fileName)
            zip.write(fullPath,fileName)

    # Delete the files.
    # TODO: Report results and submission identifiers. I should create a report, maybe save our submitted sequence .zip.
    # Give a report of what was submitted. It should be clear to the user what was submitted.
    # At the very least, just tell the user where the .zip file is. I can check what was submitted myself.
    try:
        successfulDeletion = True
        for fileName in submissionFileList:
            fullPath = join(workingDirectory, fileName)
            if isfile(fullPath):
                remove(fullPath)
            else:
                successfulDeletion = False
                raise Exception('ERROR when deleting file, it does not seem to exist:' + fullPath)



        # delete the working directory
        if(successfulDeletion):
            if isdir(workingDirectory):
                rmdir(workingDirectory)
            else:
                raise Exception('ERROR when deleting workign directory, it does not seem to exist:' + workingDirectory)

    except Exception as error:
        logging.error('ERROR when removing working directory and submission files:' + str(error))
        raise()


def getSaddlebagsDirectory():
    # Do I need to detect operating system? I don't think so.
    homeDirectory = expanduser("~")
    saddlebagsDirectory = join(homeDirectory, 'saddlebags')
    return saddlebagsDirectory



def loadConfigurationFile():
    # TODO: should I clear my configuration first? I have a method to purge my globals.
    # I don't know right now, but probably not.
    assignConfigName()

    try:

        if not isfile(globalVariables['config_file_location']):
            logging.info ('The config file does not exist yet. I will not load it:\n' + globalVariables['config_file_location'])
        else:
            logging.info ('The config file already exists, I will load it:\n' + globalVariables['config_file_location'])

            tree = ET.parse(globalVariables['config_file_location'])
            root = tree.getroot()

            for child in root:
                #logging.debug('The child tag is:' + child.tag)

                # If the child node is a submission batch
                # TODO: Think about how I can handle multiple submission batches.
                if(child.tag == 'submission_batch'):
                    submissionBatch = SubmissionBatch()

                    # Assign some information about this batch of submissions.
                    submissionBatch.enaUserName = deserializeConfigValue(child.attrib['enausername'])
                    submissionBatch.studyAccession = deserializeConfigValue(child.attrib['studyaccession'])
                    submissionBatch.chooseProject = deserializeConfigValue(child.attrib['chooseproject'])
                    submissionBatch.ipdSubmitterId = deserializeConfigValue(child.attrib['ipdsubmitterid'])
                    submissionBatch.ipdSubmitterName = deserializeConfigValue(child.attrib['ipdsubmittername'])
                    submissionBatch.ipdAltContact = deserializeConfigValue(child.attrib['ipdaltcontact'])
                    submissionBatch.ipdSubmitterEmail = deserializeConfigValue(child.attrib['ipdsubmitteremail'])
                    submissionBatch.labOfOrigin = deserializeConfigValue(child.attrib['laboforigin'])
                    submissionBatch.labContact = deserializeConfigValue(child.attrib['labcontact'])
                    submissionBatch.projectId = deserializeConfigValue(child.attrib['projectid'])
                    submissionBatch.projectShortTitle = deserializeConfigValue(child.attrib['projectshorttitle'])
                    submissionBatch.projectAbstract = deserializeConfigValue(child.attrib['projectabstract'])


                    # Loop the children, they are submission objects. Load up their information.
                    for submissionChild in child:
                        #logging.debug('The submission child tag is:' + submissionChild.tag)
                        #logging.debug('This submission has the text:' + submissionChild.text)
                        # Add a few submissions to this batch.
                        # Submission # 1
                        submission = AlleleSubmission()
                        #submission.submittedGene.fullSequence = submissionChild.text
                        submission.submittedGene = identifyGenomicFeatures(submissionChild.text)
                        submission.submittedGene.geneLocus = deserializeConfigValue(submissionChild.attrib['genelocus'])
                        submission.localAlleleName = deserializeConfigValue(submissionChild.attrib['localallelename'])
                        submission.closestAlleleWrittenDescription = deserializeConfigValue(submissionChild.attrib['closestallelewrittendescription'])
                        submission.ipdSubmissionIdentifier = deserializeConfigValue(submissionChild.attrib['ipdsubmissionidentifier'])
                        submission.ipdSubmissionVersion = deserializeConfigValue(submissionChild.attrib['ipdsubmissionversion'])
                        submission.enaAccessionIdentifier = deserializeConfigValue(submissionChild.attrib['enaaccessionidentifier'])
                        submission.cellId = deserializeConfigValue(submissionChild.attrib['cellid'])
                        submission.ethnicOrigin = deserializeConfigValue(submissionChild.attrib['ethnicorigin'])
                        submission.sex = deserializeConfigValue(submissionChild.attrib['sex'])
                        submission.consanguineous = deserializeConfigValue(submissionChild.attrib['consanguineous'])
                        submission.homozygous = deserializeConfigValue(submissionChild.attrib['homozygous'])
                        #print ('I am about to read and store my typed alleles.')
                        childElementText = submissionChild.attrib['typedalleles']
                        #print ('element text:' + childElementText)
                        deserializedText = deserializeConfigValue(childElementText)
                        #print ('deserialized text:' + deserializedText)
                        parsedObject = parseTypedAlleleInput(deserializedText)
                        #print('parsedObject:' + str(parsedObject))
                        submission.typedAlleles = parsedObject
                        #print ('Success.')
                        submission.materialAvailability = deserializeConfigValue(submissionChild.attrib['materialavailability'])
                        submission.cellBank = deserializeConfigValue(submissionChild.attrib['cellbank'])
                        submission.primarySequencingMethodology = deserializeConfigValue(submissionChild.attrib['primarysequencingmethodology'])
                        submission.secondarySequencingMethodology = deserializeConfigValue(submissionChild.attrib['secondarysequencingmethodology'])
                        submission.primerType = deserializeConfigValue(submissionChild.attrib['primertype'])
                        submission.primers = deserializeConfigValue(submissionChild.attrib['primers'])
                        submission.sequencedInIsolation = deserializeConfigValue(submissionChild.attrib['sequencedinisolation'])
                        submission.sequencingDirection = deserializeConfigValue(submissionChild.attrib['sequencingdirection'])
                        submission.numOfReactions = deserializeConfigValue(submissionChild.attrib['numofreactions'])
                        submission.methodComments = deserializeConfigValue(submissionChild.attrib['methodcomments'])
                        submission.citations = deserializeConfigValue(submissionChild.attrib['citations'])
                        submissionBatch.submissionBatch.append(submission)

                    # Store my submission batch in the global variables.
                    assignConfigurationValue('submission_batch', submissionBatch)

                else:
                    # Any arbitrary configuration value, just store it.
                    assignConfigurationValue(child.tag, child.text)


            # Here is where I assign the common/critical configuration values
            # test_submission indicates if we should use the "test" values.
            # I think I'll use this value for both ENA and IPD submissions, if it applies.
            assignIfNotExists('test_submission', '1')

            # Log levels are defined in the Saddlebags config, and passed into the python logging module.
            assignIfNotExists('logging', 'DEBUG')

            assignIfNotExists('proxy', None)

            # I'm storing FTP without the ftp:// identifier, because it is not necessary.
            # The test and prod ftp sites have the same address. This is intentional, ena doesn't have a test ftp
            # TODO : I still need this stuff? Probably. I think the act service does not need the method name anymore though.
            # TODO: I probably don't do FTP uploads anymore, i think i remove this config value.
            assignIfNotExists('ena_ftp_upload_site_test', 'webin.ebi.ac.uk')
            assignIfNotExists('ena_ftp_upload_site_prod', 'webin.ebi.ac.uk')
            assignIfNotExists('ena_rest_address_test', 'https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/')
            assignIfNotExists('ena_rest_address_prod', 'https://www.ebi.ac.uk/ena/submit/drop-box/submit/')
            #assignIfNotExists('nmdp_act_rest_address', 'http://act.b12x.org/type_align')
            assignIfNotExists('nmdp_act_rest_address', 'http://act.b12x.org')
            # TODO: i should use the nmdp configuration value when I call the GFE/ACT services. It is currently hardcoded AFAIK

            # Last step is to initialize the log files. Why is this the last step? initializing log should be first
            # but I need some config values before starting the log.
            initializeLog()
    except:
        logging.error (exc_info()[1])
        logging.error('Error when loading configuration file:' + str(globalVariables['config_file_location']) + '. Try deleting your configuration file and reload Saddlebags.')
        # TODO: Should I just delete the config file with any exception? Probably not.
