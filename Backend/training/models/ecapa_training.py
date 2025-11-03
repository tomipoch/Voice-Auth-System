#!/usr/bin/env python3
"""Script de entrenamiento ECAPA-TDNN generado automáticamente."""

import speechbrain as sb
from speechbrain.utils.distributed import run_on_main
import sys
import torch
import torchaudio
from hyperpyyaml import load_hyperpyyaml
import os
import csv

# Hyperparameters
hparams = {'seed': 1234, 'output_folder': '../models/ecapa_tdnn', 'save_folder': '../models/ecapa_tdnn/save', 'embedding_dim': 192, 'channels': [512, 512, 512, 512, 1536], 'kernel_sizes': [5, 3, 3, 3, 1], 'dilations': [1, 2, 3, 4, 1], 'attention_channels': 128, 'lin_neurons': 192, 'data_folder': './datasets/synthetic_speaker', 'train_split': 'train', 'test_split': 'test', 'sample_rate': 16000, 'number_of_epochs': 5, 'batch_size': 4, 'lr': 0.001, 'weight_decay': 0.0001, 'margin': 0.2, 'scale': 30, 'device': 'cpu'}

# Dataset preparation
@sb.utils.data_pipeline.takes("wav", "start", "stop", "spk_id")
@sb.utils.data_pipeline.provides("sig", "spk_id_encoded")
def audio_pipeline(wav, start, stop, spk_id):
    start = int(start)
    stop = int(stop)
    num_frames = stop - start
    sig, fs = torchaudio.load(wav, frame_offset=start, num_frames=num_frames)
    sig = sig.transpose(0, 1).squeeze(1)
    return sig, spk_id

# Create datasets
def dataio_prep(hparams):
    # Training data
    train_data = sb.dataio.dataset.DynamicItemDataset.from_csv(
        csv_path=hparams["train_annotation"],
        replacements={"data_root": hparams["data_folder"]},
    )
    train_data = train_data.filtered_sorted(sort_key="duration")
    
    # Validation data  
    valid_data = sb.dataio.dataset.DynamicItemDataset.from_csv(
        csv_path=hparams["valid_annotation"],
        replacements={"data_root": hparams["data_folder"]},
    )
    
    # Add pipeline
    sb.dataio.dataset.add_dynamic_item([train_data, valid_data], audio_pipeline)
    
    # Encoders
    label_encoder = sb.dataio.encoder.CategoricalEncoder()
    label_encoder.fit(train_data, valid_data, "spk_id")
    
    # Save encoders
    label_encoder.save(hparams["save_folder"])
    
    return train_data, valid_data, label_encoder

# Training Brain
class EcapaBrain(sb.Brain):
    def compute_forward(self, batch, stage):
        batch = batch.to(self.device)
        wavs, lens = batch.sig
        
        # Feature extraction and normalization
        feats = self.hparams.compute_features(wavs)
        feats = self.modules.mean_var_norm(feats, lens)
        
        # Embedding extraction
        embeddings = self.modules.embedding_model(feats, lens)
        
        # Classification
        outputs = self.modules.classifier(embeddings)
        
        return outputs, lens
    
    def compute_objectives(self, predictions, batch, stage):
        predictions, lens = predictions
        spk_id, _ = batch.spk_id_encoded
        
        # Classification loss
        loss = self.hparams.compute_cost(predictions, spk_id, lens)
        
        if stage != sb.Stage.TRAIN:
            self.error_metrics.append(batch.id, predictions, spk_id, lens)
        
        return loss
    
    def on_stage_end(self, stage, stage_loss, epoch):
        if stage == sb.Stage.TRAIN:
            self.train_loss = stage_loss
        else:
            stats = self.error_metrics.summarize("average")
            
        if stage == sb.Stage.VALID:
            # Learning rate annealing
            old_lr, new_lr = self.hparams.lr_annealing(stats["loss"])
            sb.nnet.schedulers.update_learning_rate(self.optimizer, new_lr)
            
            # Checkpointing
            self.checkpointer.save_and_keep_only(
                meta={"loss": stats["loss"]}, min_keys=["loss"]
            )

if __name__ == "__main__":
    # Run training
    train_data, valid_data, label_encoder = dataio_prep(hparams)
    
    # Create brain
    ecapa_brain = EcapaBrain(
        modules=hparams["modules"],
        opt_class=hparams["opt_class"],
        hparams=hparams,
        run_opts={"device": hparams["device"]},
        checkpointer=hparams["checkpointer"],
    )
    
    # Fit model
    ecapa_brain.fit(
        epoch_counter=ecapa_brain.hparams.epoch_counter,
        train_set=train_data,
        valid_set=valid_data,
        train_loader_kwargs=hparams["train_dataloader_opts"],
        valid_loader_kwargs=hparams["valid_dataloader_opts"],
    )
