"""Adversarial adaptation to train target encoder."""

import os

import torch
import torch.optim as optim
from torch import nn

import sound_params as params
from utils import make_variable
from utils import save_model

import tensorflow as tf

def train_tgt(src_encoder, tgt_encoder, critic,
              src_data_loader, tgt_data_loader, dataset_name):
    """Train encoder for target domain."""
    ####################
    # 1. setup network #
    ####################

    # set train state for Dropout and BN layers
    tgt_encoder.train()
    critic.train()

    # setup criterion and optimizer
    #criterion = nn.CrossEntropyLoss()
    criterion = nn.CrossEntropyLoss(weight=tf.convert_to_tensor([1, 300]))
    optimizer_tgt = optim.Adam(tgt_encoder.parameters(),
                               lr=params.c_learning_rate,
                               betas=(params.beta1, params.beta2))
    optimizer_critic = optim.Adam(critic.parameters(),
                                  lr=params.d_learning_rate,
                                  betas=(params.beta1, params.beta2))
    len_data_loader = min(len(src_data_loader), len(tgt_data_loader))

    ####################
    # 2. train network #
    ####################

    print('start training the taget models ...')

    for epoch in range(params.num_epochs):
        # zip source and target data pair
        data_zip = enumerate(zip(src_data_loader, tgt_data_loader))
        for step, ((images_src, _), (images_tgt, _)) in data_zip:
            ###########################
            # 2.1 train discriminator #
            ###########################

            # make images variable
            images_src = make_variable(images_src)
            images_tgt = make_variable(images_tgt)

            # zero gradients for optimizer
            optimizer_critic.zero_grad()

            # extract and concat features
            feat_src = src_encoder(images_src)
            feat_tgt = tgt_encoder(images_tgt)
            feat_concat = torch.cat((feat_src, feat_tgt), 0)

            # predict on discriminator
            pred_concat = critic(feat_concat.detach())

            # prepare real and fake label
            label_src = make_variable(torch.ones(feat_src.size(0)).long())
            label_tgt = make_variable(torch.zeros(feat_tgt.size(0)).long())
            label_concat = torch.cat((label_src, label_tgt), 0)

            # compute loss for critic
            loss_critic = criterion(pred_concat, label_concat)
            loss_critic.backward()

            # optimize critic

            pred_cls = torch.squeeze(pred_concat.max(1)[1])
            acc = (pred_cls == label_concat).float().mean()

            ############################
            # 2.2 train target encoder #
            ############################

            # zero gradients for optimizer
            optimizer_critic.zero_grad()
            optimizer_tgt.zero_grad()

            # extract and target features
            feat_tgt = tgt_encoder(images_tgt)

            # predict on discriminator
            pred_tgt = critic(feat_tgt)

            # prepare fake labels
            label_tgt = make_variable(torch.ones(feat_tgt.size(0)).long())

            # compute loss for target encoder
            loss_tgt = criterion(pred_tgt, label_tgt)
            loss_tgt.backward()

            # optimize target encoder
            optimizer_tgt.step()

            #######################
            # 2.3 print step info #
            #######################
            if ((step + 1) % params.log_step == 0):
                print("Epoch [{}/{}] Step [{}/{}]:"
                      "d_loss={:.5f} g_loss={:.5f} acc={:.5f}"
                      .format(epoch + 1,
                              params.num_epochs,
                              step + 1,
                              len_data_loader,
                              loss_critic.data,
                              loss_tgt.data,
                              acc.data))

        #############################
        # 2.4 save model parameters #
        #############################
        if ((epoch + 1) % params.save_step == 0):
            torch.save(critic.state_dict(), os.path.join(
                params.model_root,
                dataset_name + "-ADDA-critic-{}.pt".format(epoch + 1)))
            torch.save(tgt_encoder.state_dict(), os.path.join(
                params.model_root,
                dataset_name + "-ADDA-target-encoder-{}.pt".format(epoch + 1)))

    torch.save(critic.state_dict(), os.path.join(
        params.model_root,
        dataset_name + "-ADDA-critic-final.pt"))
    torch.save(tgt_encoder.state_dict(), os.path.join(
        params.model_root,
        dataset_name + "-ADDA-target-encoder-final.pt"))
    return tgt_encoder

def eval_src_encoder(encoder, classifier, data_loader):
    """Evaluate classifier for source domain."""
    # set eval state for Dropout and BN layers
    encoder.eval()
    classifier.eval()

    # init loss and accuracy
    loss = 0.0
    acc = 0.0

    # set loss function
    criterion = nn.CrossEntropyLoss()

    # evaluate network
    for (images, labels) in data_loader:
        images = make_variable(images, volatile=True)
        labels = make_variable(labels)

        preds = classifier(encoder(images))
        try:
            loss += criterion(preds, labels).data
        except:
            loss = criterion(preds, torch.max(labels, 1)[1]).data

        pred_cls = preds.data.max(1)[1]
        acc += pred_cls.eq(labels.data).cpu().sum()

    loss /= len(data_loader)
    acc /= len(data_loader.dataset)

    print("Avg Loss = {}, Avg Accuracy = {:2%}".format(loss, acc))


def eval_tgt_encoder(tgt_encoder, classifier, data_loader):
    """Evaluation for target encoder by source classifier on target dataset."""
    # set eval state for Dropout and BN layers
    tgt_encoder.eval()
    classifier.eval()
    # init loss and accuracy
    loss = 0.0
    acc = 0.0
    # set loss function
    criterion = nn.CrossEntropyLoss()
    # evaluate network
    for (images, labels) in data_loader:
        images = make_variable(images, volatile=True)
        labels = make_variable(labels).squeeze_()
        torch.no_grad()
        preds = classifier(tgt_encoder(images))
        loss += criterion(preds, labels).data

        pred_cls = preds.data.max(1)[1]
        acc += pred_cls.eq(labels.data).cpu().sum()
    loss /= len(data_loader)
    acc /= len(data_loader.dataset)
    print("Avg Loss = {}, Avg Accuracy = {:2%}".format(loss, acc))

def train_tgt_encoder(src_encoder, tgt_encoder, critic, src_data_loader, tgt_data_loader):
    """Train encoder for target domain."""
    ####################
    # 1. setup network #
    ####################

    # set train state for Dropout and BN layers
    tgt_encoder.train()
    critic.train()

    # setup criterion and optimizer
    #criterion = CORAL()
    criterion = nn.CrossEntropyLoss()

    optimizer_tgt = optim.Adam(tgt_encoder.parameters(),
                               lr=params.c_learning_rate,
                               betas=(params.beta1, params.beta2))
    optimizer_critic = optim.Adam(critic.parameters(),
                                  lr=params.d_learning_rate,
                                  betas=(params.beta1, params.beta2))
    len_data_loader = min(len(src_data_loader), len(tgt_data_loader))

    ####################
    # 2. train network #
    ####################

    for epoch in range(params.num_epochs):
        # zip source and target data pair
        data_zip = enumerate(zip(src_data_loader, tgt_data_loader))
        for step, ((images_src, _), (images_tgt, _)) in data_zip:
            ###########################
            # 2.1 train discriminator #
            ###########################

            # make images variable
            images_src = make_variable(images_src)
            images_tgt = make_variable(images_tgt)

            # zero gradients for optimizer
            optimizer_critic.zero_grad()

            # extract and concat features
            feat_src = src_encoder(images_src)
            feat_tgt = tgt_encoder(images_tgt)
            feat_concat = torch.cat((feat_src, feat_tgt), 0)

            # predict on discriminator
            pred_concat = critic(feat_concat.detach())

            # prepare real and fake label
            label_src = make_variable(torch.ones(feat_src.size(0)).long())
            label_tgt = make_variable(torch.zeros(feat_tgt.size(0)).long())
            label_concat = torch.cat((label_src, label_tgt), 0)

            # compute loss for critic
            loss_critic = criterion(pred_concat, label_concat)
            loss_critic.backward()

            # optimize critic

            pred_cls = torch.squeeze(pred_concat.max(1)[1])
            acc = (pred_cls == label_concat).float().mean()

            ############################
            # 2.2 train target encoder #
            ############################

            # zero gradients for optimizer
            optimizer_critic.zero_grad()
            optimizer_tgt.zero_grad()

            # extract and target features
            feat_tgt = tgt_encoder(images_tgt)

            # predict on discriminator
            pred_tgt = critic(feat_tgt)

            # prepare fake labels
            label_tgt = make_variable(torch.ones(feat_tgt.size(0)).long())

            # compute loss for target encoder
            loss_tgt = criterion(pred_tgt, label_tgt)
            loss_tgt.backward()

            # optimize target encoder
            optimizer_tgt.step()

            #######################
            # 2.3 print step info #
            #######################
            if ((step + 1) % params.log_step == 0):
                print("Epoch [{}/{}] Step [{}/{}]:"
                      "d_loss={:.5f} g_loss={:.5f} acc={:.5f}"
                      .format(epoch + 1,
                              params.num_epochs,
                              step + 1,
                              len_data_loader,
                              loss_critic.data,
                              loss_tgt.data,
                              acc.data))

        #############################
        # 2.4 save model parameters #
        #############################
        if ((epoch + 1) % params.save_step == 0):
            torch.save(critic.state_dict(), os.path.join(
                params.model_root,
                "ADDA-critic-{}.pt".format(epoch + 1)))
            torch.save(tgt_encoder.state_dict(), os.path.join(
                params.model_root,
                "ADDA-target-encoder-{}.pt".format(epoch + 1)))

    torch.save(critic.state_dict(), os.path.join(
        params.model_root,
        "ADDA-critic-final.pt"))
    torch.save(tgt_encoder.state_dict(), os.path.join(
        params.model_root,
        "ADDA-target-encoder-final.pt"))
    return tgt_encoder
