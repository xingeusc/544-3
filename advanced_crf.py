import argparse
import os
import hw3_corpus_tool
import pycrfsuite
import glob

max_iter = 70
output_verbose = False

def n_gram_feature(cur_utterance, cur_utterance_x, n):
    '''
    :param cur_utterance: is dialog_i, is the data read in
    :param cur_utterance_x: the feature list, there is no change to y
    :param n: means n gram
    :return: use cur_utterance_x, by using reference, acutally no return
    '''

    '''
        extract n_gram for token
    '''
    for i in range(0, len(cur_utterance.pos) - n + 1):
        n_gram = ''
        #get current n_gram for token
        for j in range(i, i + n):
            cur = cur_utterance.pos[j]
            n_gram += cur.token.lower() + ' '
        cur_utterance_x.append('TOKEN_'+str(n)+'_GRAM:'+n_gram[:len(n_gram) - 1])

    '''
        extract n_gram for pos
    '''
    for i in range(0, len(cur_utterance.pos) - n + 1):
        n_gram = ''
        #get current n_gram for token
        for j in range(i, i + n):
            cur = cur_utterance.pos[j]
            n_gram += cur.pos + ' '
        cur_utterance_x.append('POS_'+str(n)+'_GRAM:'+n_gram[:len(n_gram) - 1])

def dialog_feature(dialog, dialog_x, dialog_y):
    '''
    :param dialog: is a list of dialogs, is the data read in
    :param dialog_x: as a return of features of dialogs
    :param dialog_y: as y of dialogs
    :return: dialog_x, dialog_y, by using reference, actually no return
    '''
    for i in range(0, len(dialog)):
        cur_utterance = dialog[i]
        dialog_y.append(cur_utterance.act_tag)
        cur_utterance_x = []
        '''
            a feature for whether or not the speaker has changed in comparison with the previous utterance.
            a feature marking the first utterance of the dialogue.
        '''
        if(i == 0):
            cur_utterance_x.append('speaker_change:' + 'False')
            cur_utterance_x.append('first_utterance:' + 'True')
        else:
            pre_utterance = dialog[i - 1]
            if(pre_utterance.speaker != cur_utterance.speaker): cur_utterance_x.append('speaker_change:' + 'True')
            else: cur_utterance_x.append('speaker_change:' + 'False')
            cur_utterance_x.append('first_utterance:' + 'False')
        '''
        when pos = None, e.g. text = '<Laughter>', continue;, to avoid nullptr issue
        '''
        if cur_utterance.pos == None:
            dialog_x.append(cur_utterance_x)
            continue

        '''
            a feature for every token in the utterance (see the description of CRFsuite for an example).
        '''
        for j in range(0, len(cur_utterance.pos)):
            p = cur_utterance.pos[j]
            cur_utterance_x.append('TOKEN:'+p.token.lower())

        '''
            a feature for every part of speech tag in the utterance (e.g., POS_PRP POS_RB POS_VBP POS_.).
        '''
        for j in range(0, len(cur_utterance.pos)):
            p = cur_utterance.pos[j]
            cur_utterance_x.append('POS:'+p.pos)

        '''
            add new feature here
        '''
        n_gram_feature(cur_utterance, cur_utterance_x, 2)
        # n_gram_feature(cur_utterance, cur_utterance_x, 3)
        # n_gram_feature(cur_utterance, cur_utterance_x, 4)
        # n_gram_feature(cur_utterance, cur_utterance_x, 5)
        # n_gram_feature(cur_utterance, cur_utterance_x, 6)
        '''
            push the cur_utterance_x into list_x
        '''
        dialog_x.append(cur_utterance_x)


def extract_feature(data_dir, feature_list_x, feature_list_y):
    du_dict = hw3_corpus_tool.get_data(data_dir)
    dialog_filenames = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    for dialog in du_dict:
        dialog_x = []
        dialog_y = []
        dialog_feature(dialog, dialog_x, dialog_y)
        feature_list_x.append(dialog_x)
        feature_list_y.append(dialog_y)
    return dialog_filenames


def learn(input_dir):
    '''
        Feature extraction
    '''
    feature_list_x = []
    feature_list_y = []
    extract_feature(input_dir, feature_list_x, feature_list_y)

    '''
        Begin Fitting the model
    '''
    # trainer = pycrfsuite.Trainer(verbose=False)
    trainer = pycrfsuite.Trainer(verbose=output_verbose)
    for xseq, yseq in zip(feature_list_x, feature_list_y):
        trainer.append(xseq, yseq)

    trainer.set_params({
        'c1': 1.0,   # coefficient for L1 penalty
        'c2': 1e-3,  # coefficient for L2 penalty
        'max_iterations': max_iter,  # stop earlier

        # include transitions that are possible, but not observed
        'feature.possible_transitions': True
    })

    trainer.train('advanced_crf_model.crfsuite')

    # print(trainer.logparser.last_iteration)
    # print(len(trainer.logparser.iterations), end=' ')
    # print(trainer.logparser.iterations[-1])
    # print()


def classify(test_dir, output_file):
    '''
       Feature extraction
    '''
    feature_list_x = []
    feature_list_y = []
    dialog_filenames = extract_feature(test_dir, feature_list_x, feature_list_y)

    '''
        classification/tagging
    '''
    tagger = pycrfsuite.Tagger()
    tagger.open('advanced_crf_model.crfsuite')

    f = open(output_file, 'w')

    for i in range(0, len(feature_list_x)):
        utterance_tags = tagger.tag(feature_list_x[i])
        names = dialog_filenames[i].split('/')
        file_name = names[len(names) - 1]
        f.write('Filename="'+file_name+'"\n')
        for tag in utterance_tags:
            f.write(tag+'\n')
        f.write('\n')

        # print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('INPUTDIR', help='reads in a directory of CSV files (INPUTDIR), train a CRFsuite model')
    parser.add_argument('TESTDIR', help='tag the CSV files in (TESTDIR)')
    parser.add_argument('OUTPUTFILE', help='print the output labels to OUTPUTFILE')

    args = parser.parse_args()
    input_dir = args.INPUTDIR
    test_dir = args.TESTDIR
    output_file = args.OUTPUTFILE

    learn(input_dir)
    classify(test_dir, output_file)
