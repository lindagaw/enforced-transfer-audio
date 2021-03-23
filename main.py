"""Main script for ADDA."""

from six.moves import urllib
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)

import params_for_main as params
from core import eval_src, eval_tgt, train_src, train_tgt
#from models import Discriminator, GalateaEncoder, GalateaClassifier
from utils import get_data_loader, init_model, init_random_seed, make_variable, group

from source_classifier import load_chopped_source_model, load_second_half_chopped_source_model

if __name__ == '__main__':
    # init random seed
    init_random_seed(params.manual_seed)
    '''
    the purpose of this file is to test the enforced transfer + ADDA.
    dataset needed will be the testing set from CONFLICT.

    source encoder, source classifier, and target encoder should be pretrained.
    '''

    tgt_data_loader_eval = get_data_loader(params.tgt_dataset, train=False, dataset='conflict')

    for conv in [1, 2, 3, 4]:
        src_encoder, src_classifier, tgt_encoder, critic = group(conv=conv)
        probe_preds = eval_probe(critic, tgt_data_loader_eval, conv=conv)
        enforcer_preds = eval_enforcer(encoder, classifier, tgt_data_loader_eval, conv=conv)
