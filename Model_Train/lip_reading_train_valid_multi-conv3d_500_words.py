# -*- coding: utf-8 -*-
"""lip_reading_train_valid.ipynb

Author:Zhong Yuting

Model: Conv3d unit has multiple convolutional layers

Experimental Setting:Training and valid code for 500-word preprocessed dataset
"""

# mount to google colab and access to the corresponding directory
#from google.colab import drive
#drive.mount('/content/gdrive')

import os
#os.chdir("/content/gdrive/MyDrive/PRS_Project/Dataset1")

import glob
import random
import cv2
import numpy as np
from tqdm import tqdm
import argparse
import os

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import tensorflow
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.layers import (Activation, Conv3D, Dense, Dropout, Flatten,
                          MaxPooling3D)
from tensorflow.keras.layers import LeakyReLU
from tensorflow.keras.losses import categorical_crossentropy
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.utils import np_utils
from tensorflow.python.keras.utils.vis_utils import plot_model
from tensorflow.keras.utils import to_categorical
from numpy import array
from numpy import argmax
from sklearn import preprocessing
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from tensorflow.keras.callbacks import ModelCheckpoint,CSVLogger
import logging
import time

"""## **Prepare the data**"""

# data filepaths
train_video_filepaths=[]
valid_video_filepaths=[]

os.chdir("/hpctmp/e0703421/01_PRS_Dataset/train_100")
train_video_filepaths=(glob.glob("processed_**.mp4"))
os.chdir("/hpctmp/e0703421/01_PRS_Dataset/valid_30")
valid_video_filepaths=(glob.glob("processed_**.mp4"))

# random.shuffle(train_video_filepaths)
print('train data: %d' % len(train_video_filepaths),
      '\nvalid data: %d' % len(valid_video_filepaths))

train_labels=[]
train_videos=[]
valid_labels=[]
valid_videos=[]

# train data
for index in tqdm(range(0, len(train_video_filepaths))):
    cap = cv2.VideoCapture("/hpctmp/e0703421/01_PRS_Dataset/train_100/"+ train_video_filepaths[index])
    #print(train_video_filepaths[index])
    nframe = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    #print(nframe)

    if nframe != 29:
      	continue
    frames = [x for x in range(int(nframe))]
    framearray = []
    for i in range(int(nframe)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frames[i])
        ret, frame = cap.read()
        frame = cv2.resize(frame, (64, 64))
        framearray.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    
    cap.release()
    train_videos.append(np.array(framearray))

    filename=train_video_filepaths[index].split("\\")[-1]
    train_labels.append(filename.split("_")[1])

# valid data
for index in tqdm(range(0, len(valid_video_filepaths))):
    cap = cv2.VideoCapture("/hpctmp/e0703421/01_PRS_Dataset/valid_30/"+ valid_video_filepaths[index])
    #print(train_video_filepaths[index])
    #print(cap.isOpened())
    nframe = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    #print(nframe)
    if nframe != 29:
      continue
    frames = [x for x in range(int(nframe))]
    framearray = []

    for i in range(int(nframe)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frames[i])
        ret, frame = cap.read()
        frame = cv2.resize(frame, (64, 64))
        framearray.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    cap.release()
    valid_videos.append(np.array(framearray))

    filename=valid_video_filepaths[index].split("\\")[-1]
    valid_labels.append(filename.split("_")[1])

print('\ntrain videos #: %d' % len(train_videos),
      '\ntrain labels #: %d' % len(train_labels),
      '\nvalid videos #: %d' % len(valid_videos),
      '\nvalid labels #: %d' % len(valid_labels),)

"""## **Model Definition**"""

#nb_classes=35
nb_classes=500

# Define model
model = Sequential()
model.add(Conv3D(32, kernel_size=(2, 2, 2), input_shape=(29, 64, 64, 1)))
model.add(Activation('relu'))
model.add(Conv3D(32, kernel_size=(2, 2, 2)))
model.add(Activation('softmax'))
model.add(MaxPooling3D(pool_size=(2, 2, 2)))
model.add(Dropout(0.25))

model.add(Conv3D(64, kernel_size=(2, 2, 2)))
model.add(Activation('relu'))
model.add(Conv3D(64, kernel_size=(2, 2, 2)))
model.add(Activation('softmax'))
model.add(MaxPooling3D(pool_size=(2, 2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512, activation='sigmoid'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes, activation='softmax'))

model.compile(loss=categorical_crossentropy,
              optimizer=Adam(), metrics=['accuracy'])
model.summary()

"""## **One-hot Encoding**"""

le = preprocessing.LabelEncoder()
list(set(train_labels))
le.fit(list(set(train_labels)))
train_encoded_labels=le.transform(train_labels)

list(set(valid_labels))
le.fit(list(set(valid_labels)))
valid_encoded_labels=le.transform(valid_labels)

print(np.stack((np.array(train_videos),)*1, axis=-1).shape)
print(np.stack((np.array(valid_videos),)*1, axis=-1).shape)

tVideos=tensorflow.convert_to_tensor(np.stack((np.array(train_videos),)*1, axis=-1))
vVideos=tensorflow.convert_to_tensor(np.stack((np.array(valid_videos),)*1, axis=-1))
tLabels=np_utils.to_categorical(train_encoded_labels, nb_classes)
vLabels=np_utils.to_categorical(valid_encoded_labels, nb_classes)

# define example
data = train_labels
values = array(train_labels)
# print(values)
# integer encode
label_encoder = LabelEncoder()
integer_encoded = label_encoder.fit_transform(values)
# print(integer_encoded)
# binary encode
onehot_encoder = OneHotEncoder(sparse=False)
integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
onehot_encoded = onehot_encoder.fit_transform(integer_encoded)
# print(onehot_encoded)
# invert first example
inverted = label_encoder.inverse_transform([argmax(onehot_encoded[0, :])])
# print(inverted)

tVideos.shape

"""## **Logging file**"""
def log_creater(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    log_name = '{}.log'.format(time.strftime('%Y-%m-%d-%H-%M'))
    final_log_file = os.path.join(output_dir,log_name)


    # creat a log
    log = logging.getLogger('train_log')
    log.setLevel(logging.DEBUG)

    # FileHandler
    file = logging.FileHandler(final_log_file)
    file.setLevel(logging.DEBUG)

    # StreamHandler
    stream = logging.StreamHandler()
    stream.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s][line: %(lineno)d] ==> %(message)s')

    # setFormatter
    file.setFormatter(formatter)
    stream.setFormatter(formatter)

    # addHandler
    log.addHandler(file)
    log.addHandler(stream)

    log.info('creating {}'.format(final_log_file))
    return log

"""## **Traning Process and Model Saving**"""
# checkpoint
filepath ="/hpctmp/e0703421/model/model_500_11112021/model-improvement-{epoch:02d}-{val_accuracy:.2f}.hdf5"
csv_pth ="/hpctmp/e0703421/model/model_500_11112021/model-improvement-{epoch:02d}-{val_accuracy:.2f}"
checkpoint = ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
csv_logger = CSVLogger(csv_pth +'.csv') 
callbacks_list = [checkpoint,csv_logger]
#log_creater('/home/svu/e0703421/model/log')

# Fit the model
model.fit(tVideos,
          onehot_encoded,
          validation_data=(vVideos, vLabels),
          batch_size=240,
          epochs=1000, 
          callbacks=callbacks_list,
	  verbose=1,
          shuffle=True)
#test1=model.fit(tVideos,
#                onehot_encoded,
#                validation_data=(vVideos, vLabels),
#                batch_size=50, 
#                epochs=100, 
#                verbose=1, 
#                shuffle=True)

#model.save_weights('/home/svu/e0703421/model/model_')
