#from hf_cypher.cypherQuery import CypherQuery
from nose.tools import assert_equal, assert_true

#import inspect
import os
#import json

from saddlebags.AlleleSubCommon import assignConfigurationValue, writeConfigurationFile, identifyGenomicFeatures, parseExons
from saddlebags.EmblSubGenerator import EmblSubGenerator
from saddlebags.ImgtSubGenerator import ImgtSubGenerator
from saddlebags.AlleleSubCommonRest import fetchSequenceAlleleCallWithGFE


#json_file = os.path.join(os.path.dirname(__file__), '')
#file_data = open(json_file).read()
#expected = json.loads(file_data)

# To run this, activate the environment
# source /home/ben/minionvent/bin/activate
# Browse to the project folder and run nosetests.
# cd /home/ben/Github/saddlebags
# nosetests
# to see the console output (probably useful, nosetests hides all output.)
# nosetests --nocapture



def testCreateIMGTSubmissionFlatfile():
    print ('Test: Creating IMGT Flatfile')
    #assignConfigurationValue('nmdp_act_rest_address', 'http://act.b12x.org/type_align' )
    assignConfigurationValue('nmdp_act_rest_address', 'http://localhost/type_align')
    assert_true(True)
    # >HLA-A*02:01:01:12 Full Length Allele. Will we allele call correctly?
    roughFeatureSequence = 'CCAGTTCTCACTCCCATTGGGTGTCGGGTTTCCAGAGAAGCCAATCAGTGTCGTCGCGGTCGCGGTTCTAAAGTCCGCACGCACCCACCGGGACTCAGATTCTCCCCAGACGCCGAGGATGGCCGTCATGGCGCCCCGAACCCTCGTCCTGCTACTCTCGGGGGCTCTGGCCCTGACCCAGACCTGGGCGGGTGAGTGCGGGGTCGGGAGGGAAACGGCCTCTGTGGGGAGAAGCAACGGGCCCGCCTGGCGGGGGCGCAGGACCCGGGAAGCCGCGCCGGGAGGAGGGTCGGGCGGGTCTCAGCCACTCCTCGTCCCCAGGCTCTCACTCCATGAGGTATTTCTTCACATCCGTGTCCCGGCCCGGCCGCGGGGAGCCCCGCTTCATCGCAGTGGGCTACGTGGACGACACGCAGTTCGTGCGGTTCGACAGCGACGCCGCGAGCCAGAGGATGGAGCCGCGGGCGCCGTGGATAGAGCAGGAGGGTCCGGAGTATTGGGACGGGGAGACACGGAAAGTGAAGGCCCACTCACAGACTCACCGAGTGGACCTGGGGACCCTGCGCGGCTACTACAACCAGAGCGAGGCCGGTGAGTGACCCCGGCCCGGGGCGCAGGTCACGACCTCTCATCCCCCACGGACGGGCCAGGTCGCCCACAGTCTCCGGGTCCGAGATCCGCCCCGAAGCCGCGGGACCCCGAGACCCTTGCCCCGGGAGAGGCCCAGGCGCCTTTACCCGGTTTCATTTTCAGTTTAGGCCAAAAATCCCCCCAGGTTGGTCGGGGCGGGGCGGGGCTCGGGGGACCGGGCTGACCGCGGGGTCCGGGCCAGGTTCTCACACCGTCCAGAGGATGTATGGCTGCGACGTGGGGTCGGACTGGCGCTTCCTCCGCGGGTACCACCAGTACGCCTACGACGGCAAGGATTACATCGCCCTGAAAGAGGACCTGCGCTCTTGGACCGCGGCGGACATGGCAGCTCAGACCACCAAGCACAAGTGGGAGGCGGCCCATGTGGCGGAGCAGTTGAGAGCCTACCTGGAGGGCACGTGCGTGGAGTGGCTCCGCAGATACCTGGAGAACGGGAAGGAGACGCTGCAGCGCACGGGTACCAGGGGCCACGGGGCGCCTCCCTGATCGCCTGTAGATCTCCCGGGCTGGCCTCCCACAAGGAGGGGAGACAATTGGGACCAACACTAGAATATCGCCCTCCCTCTGGTCCTGAGGGAGAGGAATCCTCCTGGGTTTCCAGATCCTGTACCAGAGAGTGACTCTGAGGTTCCGCCCTGCTCTCTGACACAATTAAGGGATAAAATCTCTGAAGGAATGACGGGAAGACGATCCCTCGAATACTGATGAGTGGTTCCCTTTGACACACACAGGCAGCAGCCTTGGGCCCGTGACTTTTCCTCTCAGGCCTTGTTCTCTGCTTCACACTCAATGTGTGTGGGGGTCTGAGTCCAGCACTTCTGAGTCCTTCAGCCTCCACTCAGGTCAGGACCAGAAGTCGCTGTTCCCTCTTCAGGGACTAGAATTTTCCACGGAATAGGAGATTATCCCAGGTGCCTGTGTCCAGGCTGGTGTCTGGGTTCTGTGCTCCCTTCCCCATCCCAGGTGTCCTGTCCATTCTCAAGATAGCCACATGTGTGCTGGAGGAGTGTCCCATGACAGACGCAAAATGCCTGAATGATCTGACTCTTCCTGACAGACGCCCCCAAAACGCATATGACTCACCACGCTGTCTCTGACCATGAAGCCACCCTGAGGTGCTGGGCCCTGAGCTTCTACCCTGCGGAGATCACACTGACCTGGCAGCGGGATGGGGAGGACCAGACCCAGGACACGGAGCTCGTGGAGACCAGGCCTGCAGGGGATGGAACCTTCCAGAAGTGGGCGGCTGTGGTGGTGCCTTCTGGACAGGAGCAGAGATACACCTGCCATGTGCAGCATGAGGGTTTGCCCAAGCCCCTCACCCTGAGATGGGGTAAGGAGGGAGACGGGGGTGTCATGTCTTTTAGGGAAAGCAGGAGCCTCTCTGACCTTTAGCAGGGTCAGGGCCCCTCACCTTCCCCTCTTTTCCCAGAGCCGTCTTCCCAGCCCACCATCCCCATCGTGGGCATCATTGCTGGCCTGGTTCTCTTTGGAGCTGTGATCACTGGAGCTGTGGTCGCTGCTGTGATGTGGAGGAGGAAGAGCTCAGGTGGGGAAGGGGTGAAGGGTGGGTCTGAGATTTCTTGTCTCACTGAGGGTTCCAAGACCCAGGTAGAAGTGTGCCCTGCCTCGTTACTGGGAAGCACCACCCACAATTATGGGCCTACCCAGCCTGGGCCCTGTGTGCCAGCACTTACTCTTTTGTAAAGCACCTGTTAAAATGAAGGACAGATTTATCACCTTGATTACAGCGGTGATGGGACCTGATCCCAGCAGTCACAAGTCACAGGGGAAGGTCCCTGAGGACCTTCAGGAGGGCGGTTGGTCCAGGACCCACACCTGCTTTCTTCATGTTTCCTGATCCCGCCCTGGGTCTGCAGTCACACATTTCTGGAAACTTCTCTGAGGTCCAAGACTTGGAGGTTCCTCTAGGACCTTAAGGCCCTGACTCCTTTCTGGTATCTCACAGGACATTTTCTTCCCACAGATAGAAAAGGAGGGAGCTACTCTCAGGCTGCAAGTAAGTATGAAGGAGGCTGATGCCTGAGGTCCTTGGGATATTGTGTTTGGGAGCCCATGGGGGAGCTCACCCACCCCACAATTCCTCCTCTAGCCACATCTTCTGTGGGATCTGACCAGGTTCTGTTTTTGTTCTACCCCAGGCAGTGACAGTGCCCAGGGCTCTGATGTGTCTCTCACAGCTTGTAAAGGTGAGAGCCTGGAGGGCCTGATGTGTGTTGGGTGTTGGGCGGAACAGTGGACACAGCTGTGCTGTGGGGTTTCTTTCCATTGGATGTATTGAGCATGCGATGGGCTGTTTAAAGTGTGACCCCTCACTGTGACAGATACGAATTTGTTCATGAATATTTTTTTCTATAGTGTGAGACAGCTGCCTTGTGTGGGACTGAGAGGCAAGAGTTGTTCCTGCCCTTCCCTTTGTGACTTGAAGAACCCTGACTTTGTTTCTGCAAAGGCACCTGCATGTGTCTGTGTTCGTGTAGGCATAATGTGAGGAGGTGGGGAGACCACCCCACCCCCATGTCCACCATGACCCTCTTCCCACGCTGACCTGTGCTCCCTCCCCAATCATCTTTCCTGTTCCAGAGAGGTGGGGCTGAGGTGTCTCCATCTCTGTCTCAACTTCATGGTGCACTGAGCTGTAACTTCTTCCTTCCCTATTAAAA'
    hlaLocus = 'HLA-A'
    # roughFeatureSequence = 'aag\nCGTCGT\nccg\nGGCTGA\naat'
    alleleCallWithGFE = fetchSequenceAlleleCallWithGFE(roughFeatureSequence, hlaLocus)
    assert_true(len(alleleCallWithGFE) > 3)

    # print 'ALLELE CALL RESULTS:'
    # print alleleCallWithGFE

    annotatedSequence = parseExons(roughFeatureSequence, alleleCallWithGFE)
    #print ('ANNOTATED SEQUENCE:')
    #print (annotatedSequence)
    assert_true(len(annotatedSequence) > 3)

    imgtGenerator = ImgtSubGenerator()

    imgtGenerator.sequenceAnnotation = identifyGenomicFeatures(annotatedSequence)

    assignConfigurationValue('imgt_submission_identifier', 'Fake_IMGTHLA_Sub_ID')
    assignConfigurationValue('imgt_submission_version', '1')
    # I think I dont need this embl release date.
    #assignConfigurationValue('embl_release_date', '09/08/2017')
    assignConfigurationValue('allele_name', 'HLA-A_NEW_1')
    # I need a method to do this...I am adding it now.
    #assignConfigurationValue('closest_allele_written_description', 'TEMP_IMGTHLA_IDENTIFIER')
    assignConfigurationValue('embl_sequence_accession', 'Fake_EMBL_Seq_Acc')
    assignConfigurationValue('imgt_submitter_id', 'Fake_IMGTHLA_Submitter_ID')
    assignConfigurationValue('imgt_submitter_name', 'Fake_IMGTHLA_Submitter_Name')
    assignConfigurationValue('imgt_alt_contact', 'Fake_IMGTHLA_Alt_Contact')
    assignConfigurationValue('imgt_submitter_email', 'Fake_IMGTHLA_Email')
    assignConfigurationValue('cell_id', 'Fake_Cell_ID')
    assignConfigurationValue('ethnic_origin', 'African American')
    assignConfigurationValue('sex', 'Unknown')
    assignConfigurationValue('consanguineous', 'Unknown')
    assignConfigurationValue('homozygous', 'Unknown')
    assignConfigurationValue('lab_of_origin', 'Maastricht University Medical Center')
    assignConfigurationValue('lab_contact', 'Marspel JR Spilanus')
    assignConfigurationValue('alleles','HLA-A*01:01:01:01;HLA-B*40:72:01')
    assignConfigurationValue('material_availability', 'No Material Available')
    assignConfigurationValue('cell_bank', 'Not Available')
    assignConfigurationValue('primary_sequencing_methodology', 'Direct sequencing of PCR product from DNA (SBT)')
    assignConfigurationValue('secondary_sequencing_methodology', 'Direct sequencing of PCR product from DNA (SBT)')
    assignConfigurationValue('primer_type', 'Both allele and locus specific')
    assignConfigurationValue('primers', '03PID03     CCCAAAGGGTTTCCCGGGAAATTT 3UT 3015-3042;04PID04     AAAGGGTTTCCCGGGAAATTTCCC 5UT 4015-4042')
    assignConfigurationValue('sequenced_in_isolation', 'Yes')
    assignConfigurationValue('no_of_reactions', '3')
    assignConfigurationValue('method_comments', 'The method we used was MinION sequencing!')
    #assignConfigurationValue('closest_known_allele', 'TEMP_IMGTHLA_IDENTIFIER')

    imgtSubmission = imgtGenerator.buildIMGTSubmission()

    print('IMGT SUBMISSION:\n' + imgtSubmission)

    assert_true(len(imgtSubmission) > 3)
    assert_true(imgtSubmission is not None)

    # Maybe I don't want to safe my configuration with all these test values but maybe I don't care :D
    writeConfigurationFile()


def testCreateEMBLSubmissionFlatfile():
    print ('Test: Create an EMBL SubmissionFlatfile')
    assert_true(True)

    roughFeatureSequence = 'aag\nCGTCGT\nccg\nGGCTGA\naat'

    assignConfigurationValue('sample_id', 'Donor_12345')
    assignConfigurationValue('gene', 'HLA-C')
    assignConfigurationValue('class', '1')
    assignConfigurationValue('allele_name', 'Allele:01:02')

    allGen = EmblSubGenerator()
    # roughFeatureSequence = self.featureInputGuiObject.get('1.0', 'end')

    allGen.sequenceAnnotation = identifyGenomicFeatures(roughFeatureSequence)

    enaSubmission = allGen.buildENASubmission()

    assert_true(len(enaSubmission) > 3)
    assert_true(enaSubmission is not None)
                
def testAnnotateRoughSequence():
    print ('Test: Annotate a rough sequence using GFE')
    #assignConfigurationValue('nmdp_act_rest_address', 'http://act.b12x.org/type_align' )
    assignConfigurationValue('nmdp_act_rest_address', 'http://localhost/type_align')
    assert_true(True)
    #>HLA-A*02:01:01:12 Full Length Allele. Will we allele call correctly?
    roughFeatureSequence = 'CCAGTTCTCACTCCCATTGGGTGTCGGGTTTCCAGAGAAGCCAATCAGTGTCGTCGCGGTCGCGGTTCTAAAGTCCGCACGCACCCACCGGGACTCAGATTCTCCCCAGACGCCGAGGATGGCCGTCATGGCGCCCCGAACCCTCGTCCTGCTACTCTCGGGGGCTCTGGCCCTGACCCAGACCTGGGCGGGTGAGTGCGGGGTCGGGAGGGAAACGGCCTCTGTGGGGAGAAGCAACGGGCCCGCCTGGCGGGGGCGCAGGACCCGGGAAGCCGCGCCGGGAGGAGGGTCGGGCGGGTCTCAGCCACTCCTCGTCCCCAGGCTCTCACTCCATGAGGTATTTCTTCACATCCGTGTCCCGGCCCGGCCGCGGGGAGCCCCGCTTCATCGCAGTGGGCTACGTGGACGACACGCAGTTCGTGCGGTTCGACAGCGACGCCGCGAGCCAGAGGATGGAGCCGCGGGCGCCGTGGATAGAGCAGGAGGGTCCGGAGTATTGGGACGGGGAGACACGGAAAGTGAAGGCCCACTCACAGACTCACCGAGTGGACCTGGGGACCCTGCGCGGCTACTACAACCAGAGCGAGGCCGGTGAGTGACCCCGGCCCGGGGCGCAGGTCACGACCTCTCATCCCCCACGGACGGGCCAGGTCGCCCACAGTCTCCGGGTCCGAGATCCGCCCCGAAGCCGCGGGACCCCGAGACCCTTGCCCCGGGAGAGGCCCAGGCGCCTTTACCCGGTTTCATTTTCAGTTTAGGCCAAAAATCCCCCCAGGTTGGTCGGGGCGGGGCGGGGCTCGGGGGACCGGGCTGACCGCGGGGTCCGGGCCAGGTTCTCACACCGTCCAGAGGATGTATGGCTGCGACGTGGGGTCGGACTGGCGCTTCCTCCGCGGGTACCACCAGTACGCCTACGACGGCAAGGATTACATCGCCCTGAAAGAGGACCTGCGCTCTTGGACCGCGGCGGACATGGCAGCTCAGACCACCAAGCACAAGTGGGAGGCGGCCCATGTGGCGGAGCAGTTGAGAGCCTACCTGGAGGGCACGTGCGTGGAGTGGCTCCGCAGATACCTGGAGAACGGGAAGGAGACGCTGCAGCGCACGGGTACCAGGGGCCACGGGGCGCCTCCCTGATCGCCTGTAGATCTCCCGGGCTGGCCTCCCACAAGGAGGGGAGACAATTGGGACCAACACTAGAATATCGCCCTCCCTCTGGTCCTGAGGGAGAGGAATCCTCCTGGGTTTCCAGATCCTGTACCAGAGAGTGACTCTGAGGTTCCGCCCTGCTCTCTGACACAATTAAGGGATAAAATCTCTGAAGGAATGACGGGAAGACGATCCCTCGAATACTGATGAGTGGTTCCCTTTGACACACACAGGCAGCAGCCTTGGGCCCGTGACTTTTCCTCTCAGGCCTTGTTCTCTGCTTCACACTCAATGTGTGTGGGGGTCTGAGTCCAGCACTTCTGAGTCCTTCAGCCTCCACTCAGGTCAGGACCAGAAGTCGCTGTTCCCTCTTCAGGGACTAGAATTTTCCACGGAATAGGAGATTATCCCAGGTGCCTGTGTCCAGGCTGGTGTCTGGGTTCTGTGCTCCCTTCCCCATCCCAGGTGTCCTGTCCATTCTCAAGATAGCCACATGTGTGCTGGAGGAGTGTCCCATGACAGATGCAAAATGCCTGAATGATCTGACTCTTCCTGACAGACGCCCCCAAAACGCATATGACTCACCACGCTGTCTCTGACCATGAAGCCACCCTGAGGTGCTGGGCCCTGAGCTTCTACCCTGCGGAGATCACACTGACCTGGCAGCGGGATGGGGAGGACCAGACCCAGGACACGGAGCTCGTGGAGACCAGGCCTGCAGGGGATGGAACCTTCCAGAAGTGGGCGGCTGTGGTGGTGCCTTCTGGACAGGAGCAGAGATACACCTGCCATGTGCAGCATGAGGGTTTGCCCAAGCCCCTCACCCTGAGATGGGGTAAGGAGGGAGACGGGGGTGTCATGTCTTTTAGGGAAAGCAGGAGCCTCTCTGACCTTTAGCAGGGTCAGGGCCCCTCACCTTCCCCTCTTTTCCCAGAGCCGTCTTCCCAGCCCACCATCCCCATCGTGGGCATCATTGCTGGCCTGGTTCTCTTTGGAGCTGTGATCACTGGAGCTGTGGTCGCTGCTGTGATGTGGAGGAGGAAGAGCTCAGGTGGGGAAGGGGTGAAGGGTGGGTCTGAGATTTCTTGTCTCACTGAGGGTTCCAAGACCCAGGTAGAAGTGTGCCCTGCCTCGTTACTGGGAAGCACCACCCACAATTATGGGCCTACCCAGCCTGGGCCCTGTGTGCCAGCACTTACTCTTTTGTAAAGCACCTGTTAAAATGAAGGACAGATTTATCACCTTGATTACAGCGGTGATGGGACCTGATCCCAGCAGTCACAAGTCACAGGGGAAGGTCCCTGAGGACCTTCAGGAGGGCGGTTGGTCCAGGACCCACACCTGCTTTCTTCATGTTTCCTGATCCCGCCCTGGGTCTGCAGTCACACATTTCTGGAAACTTCTCTGAGGTCCAAGACTTGGAGGTTCCTCTAGGACCTTAAGGCCCTGACTCCTTTCTGGTATCTCACAGGACATTTTCTTCCCACAGATAGAAAAGGAGGGAGCTACTCTCAGGCTGCAAGTAAGTATGAAGGAGGCTGATGCCTGAGGTCCTTGGGATATTGTGTTTGGGAGCCCATGGGGGAGCTCACCCACCCCACAATTCCTCCTCTAGCCACATCTTCTGTGGGATCTGACCAGGTTCTGTTTTTGTTCTACCCCAGGCAGTGACAGTGCCCAGGGCTCTGATGTGTCTCTCACAGCTTGTAAAGGTGAGAGCCTGGAGGGCCTGATGTGTGTTGGGTGTTGGGCGGAACAGTGGACACAGCTGTGCTGTGGGGTTTCTTTCCATTGGATGTATTGAGCATGCGATGGGCTGTTTAAAGTGTGACCCCTCACTGTGACAGATACGAATTTGTTCATGAATATTTTTTTCTATAGTGTGAGACAGCTGCCTTGTGTGGGACTGAGAGGCAAGAGTTGTTCCTGCCCTTCCCTTTGTGACTTGAAGAACCCTGACTTTGTTTCTGCAAAGGCACCTGCATGTGTCTGTGTTCGTGTAGGCATAATGTGAGGAGGTGGGGAGACCACCCCACCCCCATGTCCACCATGACCCTCTTCCCACGCTGACCTGTGCTCCCTCCCCAATCATCTTTCCTGTTCCAGAGAGGTGGGGCTGAGGTGTCTCCATCTCTGTCTCAACTTCATGGTGCACTGAGCTGTAACTTCTTCCTTCCCTATTAAAA'
    hlaLocus = 'HLA-A'
    #roughFeatureSequence = 'aag\nCGTCGT\nccg\nGGCTGA\naat'
    alleleCallWithGFE = fetchSequenceAlleleCallWithGFE(roughFeatureSequence, hlaLocus)
    assert_true(len(alleleCallWithGFE) > 3)

    #print 'ALLELE CALL RESULTS:'
    #print alleleCallWithGFE

    annotatedSequence = parseExons(roughFeatureSequence, alleleCallWithGFE)
    print ('ANNOTATED SEQUENCE:')
    print (annotatedSequence)
    assert_true(len(annotatedSequence) > 3)
    
def testAnnotateNOVELSequence():
    print ('Test: Annotate a NOVEL SEQUENCE USING GFE')
    #assignConfigurationValue('nmdp_act_rest_address', 'http://act.b12x.org/type_align' )
    assignConfigurationValue('nmdp_act_rest_address', 'http://localhost/type_align' )
    assert_true(True)
    #> HLA-A*02:01:01:12 with single SNP.
    roughFeatureSequence = 'CCAGTTCTCACTCCCATTGGGTGTCGGGTTTCCAGAGAAGCCAATCAGTGTCGTCGCGGTCGCGGTTCTAAAGTCCGCACGCACCCACCGGGACTCAGATTCTCCCCAGACGCCGAGGATGGCCGTCATGGCGCCCCGAACCCTCGTCCTGCTACTCTCGGGGGCTCTGGCCCTGACCCAGACCTGGGCGGGTGAGTGCGGGGTCGGGAGGGAAACGGCCTCTGTGGGGAGAAGCAACGGGCCCGCCTGGCGGGGGCGCAGGACCCGGGAAGCCGCGCCGGGAGGAGGGTCGGGCGGGTCTCAGCCACTCCTCGTCCCCAGGCTCTCACTCCATGAGGTATTTCTTCACATCCGTGTCCCGGCCCGGCCGCGGGGAGCCCCGCTTCATCGCAGTGGGCTACGTGGACGACACGCAGTTCGTGCGGTTCGACAGCGACGCCGCGAGCCAGAGGATGGAGCCGCGGGCGCCGTGGATAGAGCAGGAGGGTCCGGAGTATTGGGACGGGGAGACACGGAAAGTGAAGGCCCACTCACAGACTCACCGAGTGGACCTGGGGACCCTGCGCGGCTACTACAACCAGAGCGAGGCCGGTGAGTGACCCCGGCCCGGGGCGCAGGTCACGACCTCTCATCCCCCACGGACGGGCCAGGTCGCCCACAGTCTCCGGGTCCGAGATCCGCCCCGAAGCCGCGGGACCCCGAGACCCTTGCCCCGGGAGAGGCCCAGGCGCCTTTACCCGGTTTCATTTTCAGTTTAGGCCAAAAATCCCCCCAGGTTGGTCGGGGCGGGGCGGGGCTCGGGGGACCGGGCTGACCGCGGGGTCCGGGCCAGGTTCTCACACCGTCCAGAGGATGTATGGCTGCGACGTGGGGTCGGACTGGCGCTTCCTCCGCGGGTACCACCAGTACGCCTACGACGGCAAGGATTACATCGCCCTGAAAGAGGACCTGCGCTCTTGGACCGCGGCGGACATGGCAGCTCAGACCACCAAGCACAAGTGGGAGGCGGCCCATGTGGCGGAGCAGTTGAGAGCCTACCTGGAGGGCACGTGCGTGGAGTGGCTCCGCAGATACCTGGAGAACGGGAAGGAGACGCTGCAGCGCACGGGTACCAGGGGCCACGGGGCGCCTCCCTGATCGCCTGTAGATCTCCCGGGCTGGCCTCCCACAAGGAGGGGAGACAATTGGGACCAACACTAGAATATCGCCCTCCCTCTGGTCCTGAGGGAGAGGAATCCTCCTGGGTTTCCAGATCCTGTACCAGAGAGTGACTCTGAGGTTCCGCCCTGCTCTCTGACACAATTAAGGGATAAAATCTCTGAAGGAATGACGGGAAGACGATCCCTCGAATACTGATGAGTGGTTCCCTTTGACACACACAGGCAGCAGCCTTGGGCCCGTGACTTTTCCTCTCAGGCCTTGTTCTCTGCTTCACACTCAATGTGTGTGGGGGTCTGAGTCCAGCACTTCTGAGTCCTTCAGCCTCCACTCAGGTCAGGACCAGAAGTCGCTGTTCCCTCTTCAGGGACTAGAATTTTCCACGGAATAGGAGATTATCCCAGGTGCCTGTGTCCAGGCTGGTGTCTGGGTTCTGTGCTCCCTTCCCCATCCCAGGTGTCCTGTCCATTCTCAAGATAGCCACATGTGTGCTGGAGGAGTGTCCCATGACAGACGCAAAATGCCTGAATGATCTGACTCTTCCTGACAGACGCCCCCAAAACGCATATGACTCACCACGCTGTCTCTGACCATGAAGCCACCCTGAGGTGCTGGGCCCTGAGCTTCTACCCTGCGGAGATCACACTGACCTGGCAGCGGGATGGGGAGGACCAGACCCAGGACACGGAGCTCGTGGAGACCAGGCCTGCAGGGGATGGAACCTTCCAGAAGTGGGCGGCTGTGGTGGTGCCTTCTGGACAGGAGCAGAGATACACCTGCCATGTGCAGCATGAGGGTTTGCCCAAGCCCCTCACCCTGAGATGGGGTAAGGAGGGAGACGGGGGTGTCATGTCTTTTAGGGAAAGCAGGAGCCTCTCTGACCTTTAGCAGGGTCAGGGCCCCTCACCTTCCCCTCTTTTCCCAGAGCCGTCTTCCCAGCCCACCATCCCCATCGTGGGCATCATTGCTGGCCTGGTTCTCTTTGGAGCTGTGATCACTGGAGCTGTGGTCGCTGCTGTGATGTGGAGGAGGAAGAGCTCAGGTGGGGAAGGGGTGAAGGGTGGGTCTGAGATTTCTTGTCTCACTGAGGGTTCCAAGACCCAGGTAGAAGTGTGCCCTGCCTCGTTACTGGGAAGCACCACCCACAATTATGGGCCTACCCAGCCTGGGCCCTGTGTGCCAGCACTTACTCTTTTGTAAAGCACCTGTTAAAATGAAGGACAGATTTATCACCTTGATTACAGCGGTGATGGGACCTGATCCCAGCAGTCACAAGTCACAGGGGAAGGTCCCTGAGGACCTTCAGGAGGGCGGTTGGTCCAGGACCCACACCTGCTTTCTTCATGTTTCCTGATCCCGCCCTGGGTCTGCAGTCACACATTTCTGGAAACTTCTCTGAGGTCCAAGACTTGGAGGTTCCTCTAGGACCTTAAGGCCCTGACTCCTTTCTGGTATCTCACAGGACATTTTCTTCCCACAGATAGAAAAGGAGGGAGCTACTCTCAGGCTGCAAGTAAGTATGAAGGAGGCTGATGCCTGAGGTCCTTGGGATATTGTGTTTGGGAGCCCATGGGGGAGCTCACCCACCCCACAATTCCTCCTCTAGCCACATCTTCTGTGGGATCTGACCAGGTTCTGTTTTTGTTCTACCCCAGGCAGTGACAGTGCCCAGGGCTCTGATGTGTCTCTCACAGCTTGTAAAGGTGAGAGCCTGGAGGGCCTGATGTGTGTTGGGTGTTGGGCGGAACAGTGGACACAGCTGTGCTGTGGGGTTTCTTTCCATTGGATGTATTGAGCATGCGATGGGCTGTTTAAAGTGTGACCCCTCACTGTGACAGATACGAATTTGTTCATGAATATTTTTTTCTATAGTGTGAGACAGCTGCCTTGTGTGGGACTGAGAGGCAAGAGTTGTTCCTGCCCTTCCCTTTGTGACTTGAAGAACCCTGACTTTGTTTCTGCAAAGGCACCTGCATGTGTCTGTGTTCGTGTAGGCATAATGTGAGGAGGTGGGGAGACCACCCCACCCCCATGTCCACCATGACCCTCTTCCCACGCTGACCTGTGCTCCCTCCCCAATCATCTTTCCTGTTCCAGAGAGGTGGGGCTGAGGTGTCTCCATCTCTGTCTCAACTTCATGGTGCACTGAGCTGTAACTTCTTCCTTCCCTATTAAAA'
    hlaLocus = 'HLA-A'
    #roughFeatureSequence = 'aag\nCGTCGT\nccg\nGGCTGA\naat'
    alleleCallWithGFE = fetchSequenceAlleleCallWithGFE(roughFeatureSequence, hlaLocus)
    assert_true(len(alleleCallWithGFE) > 3)
    
    #print 'ALLELE CALL RESULTS:'
    #print alleleCallWithGFE
    
    
    annotatedSequence = parseExons(roughFeatureSequence, alleleCallWithGFE)
    print ('ANNOTATED SEQUENCE:')
    print (annotatedSequence)
    assert_true(len(annotatedSequence) > 3)
    
    
    