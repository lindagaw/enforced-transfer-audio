"""Main script for ADDA."""

from six.moves import urllib
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)

import sound_params as params
from core import eval_src, eval_tgt, train_src, train_tgt, eval_tgt_ood, train_tgt_classifier
from core import get_distribution, eval_ADDA, eval_ADDA_no_ood
from models import Discriminator, GalateaEncoder, GalateaClassifier

from models import AurielEncoder, BeatriceEncoder, CielEncoder, DioneEncoder
from models import AurielClassifier, BeatriceClassifier, CielClassifier, DioneClassifier
from utils import get_data_loader, init_model, init_random_seed

import sys, pretty_errors

if __name__ == '__main__':
    # init random seed
    init_random_seed(params.manual_seed)

    #activations = ['CONV_1_ACTIVATIONS', 'CONV_2_ACTIVATIONS', 'CONV_3_ACTIVATIONS', 'CONV_4_ACTIVATIONS']

    try:
        params.src_dataset = str(sys.argv[1])
        params.tgt_dataset = str(sys.argv[1])
    except:
        raise RuntimeError('must specify src and trg names in the form of \
                            python enforced_tf_main.py src_name_string, tgt_name_string.')

    print('src_dataset is the ' + params.src_dataset + ' of samples in emotion dataset (source).')
    print('tgt_dataset is the ' + params.tgt_dataset + ' of samples in conflict dataset (target).')
    # load dataset
    src_data_loader = get_data_loader(params.src_dataset, dataset='emotion')
    src_data_loader_eval = get_data_loader(params.src_dataset, train=False, dataset='emotion')
    tgt_data_loader = get_data_loader(params.tgt_dataset, dataset='conflict')
    tgt_data_loader_eval = get_data_loader(params.tgt_dataset, train=False, dataset='conflict')

    if '0' in str(sys.argv[1]):
        src_encoder_net = GalateaEncoder()
        src_classifier_net = GalateaClassifier()
        tgt_classifier_net = GalateaClassifier()
        tgt_encoder_net = GalateaEncoder()

    elif '1' in str(sys.argv[1]):
        src_encoder_net = AurielEncoder()
        src_classifier_net = AurielClassifier()
        tgt_classifier_net = AurielClassifier()
        tgt_encoder_net = AurielEncoder()
    elif '2' in str(sys.argv[1]):
        src_encoder_net = BeatriceEncoder()
        src_classifier_net = BeatriceClassifier()
        tgt_classifier_net = BeatriceClassifier()
        tgt_encoder_net = BeatriceEncoder()
    elif '3' in str(sys.argv[1]):
        src_encoder_net = CielEncoder()
        src_classifier_net = CielClassifier()
        tgt_classifier_net = CielClassifier()
        tgt_encoder_net = CielEncoder()
    else:
        src_encoder_net = DioneEncoder()
        src_classifier_net = DioneClassifier()
        tgt_classifier_net = DioneClassifier()
        tgt_encoder_net = DioneEncoder()
    # load models
    src_encoder = init_model(net=src_encoder_net,
                             restore=params.src_encoder_restore)

    src_classifier = init_model(net=src_classifier_net,
                                restore=params.src_classifier_restore)

    tgt_classifier = init_model(net=tgt_classifier_net,
                                restore=params.tgt_classifier_restore)

    tgt_encoder = init_model(net=tgt_encoder_net,
                             restore=params.tgt_encoder_restore)


    critic = init_model(Discriminator(input_dims=params.d_input_dims,
                                      hidden_dims=params.d_hidden_dims,
                                      output_dims=params.d_output_dims),
                        restore=params.d_model_restore)


    # train source model
    print("=== Training classifier for source domain ===")
    print(">>> Source Encoder <<<")
    print(src_encoder)
    print(">>> Source Classifier <<<")
    print(src_classifier)


    src_encoder, src_classifier = train_src(
        src_encoder,
        src_classifier,
        src_data_loader, dataset_name=params.src_dataset)

    # eval source model
    print("=== Evaluating classifier for source domain ===")
    eval_src(src_encoder, src_classifier, src_data_loader_eval)

    # train target encoder by GAN
    print("=== Training encoder for target domain ===")
    print(">>> Target Encoder <<<")
    print(tgt_encoder)
    print(">>> Critic <<<")
    print(critic)

    # init weights of target encoder with those of source encoder
    if not tgt_encoder.restored:
        tgt_encoder.load_state_dict(src_encoder.state_dict())

    if not (tgt_encoder.restored and critic.restored and
            params.tgt_model_trained):
        tgt_encoder = train_tgt(src_encoder, tgt_encoder, critic,
                                src_data_loader, tgt_data_loader, dataset_name=params.tgt_dataset)

    tgt_encoder, tgt_classifier = train_tgt_classifier(tgt_encoder, tgt_classifier, tgt_data_loader)

    # eval target encoder on test set of target dataset
    print("=== Evaluating classifier for encoded target domain ===")
    print(">>> source only <<<")
    eval_tgt(src_encoder, src_classifier, tgt_data_loader_eval)
    print(">>> domain adaption <<<")
    eval_tgt(tgt_encoder, tgt_classifier, tgt_data_loader_eval)

    get_distribution(src_encoder, tgt_encoder, src_classifier, tgt_classifier, critic, src_data_loader, 'src')
    get_distribution(src_encoder, tgt_encoder, src_classifier, tgt_classifier, critic, tgt_data_loader, 'tgt')

    print(">>> out of distribution and domain adaptation <<<")
    eval_ADDA(src_encoder, tgt_encoder, src_classifier, tgt_classifier, critic, tgt_data_loader_eval)

    print(">>> domain adaptation no OOD <<<")
    eval_ADDA_no_ood(src_encoder, tgt_encoder, src_classifier, tgt_classifier, critic, tgt_data_loader_eval)

    #eval_tgt_ood(src_encoder, tgt_encoder, src_classifier, tgt_classifier, src_data_loader, tgt_data_loader, tgt_data_loader_eval)
