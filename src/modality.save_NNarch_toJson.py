"""
===============================================
Define and save the Neural Network architecture
===============================================

We developed two sequential neural networks to identify the brain MRI contrast.  The first network was a convolutional neural network that inferred the modality on a sagittal slice.  The second network combined the result generated by the first nerwork to infer the modality on the entire volume.  

This script was used to define the architectures of the two networks and save them as .json string files to later be loaded during the training and testing phase.  The architecture can be modified to meet different requirements including data size, number of classes (MRI contrast) to model, and architecture parameters.  Upon execution this script saves .json files the specify the neural network acrhitecture.

"""
print(__doc__)

import json
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, BatchNormalization
from keras.layers import Conv2D, MaxPooling2D


def getCNN(nb_classes=8,input_shape=(1,32,32)):

    # Define the model architecture: layers, parameters, etc...
    # nb_classes=8, is the number of MRI contrasts the algorithm models
    # input_shape=(1,32,32), is the dimension of one sagittal slice

    model = Sequential()

    model.add(Conv2D(32, (3, 3), padding='same', input_shape=input_shape,name='convo2D_000'))
    model.add(BatchNormalization(axis=1,name='batch_001'))
    model.add(Activation('relu',name='relu_002'))
    model.add(Conv2D(32, (3, 3),name='convo2D_003'))
    model.add(BatchNormalization(axis=1,name='batch_004'))
    model.add(Activation('relu',name='relu_005'))
    model.add(MaxPooling2D(pool_size=(2, 2),name='pool_006'))

    model.add(Conv2D(64, (3, 3), padding='same',name='convo2D_007'))
    model.add(BatchNormalization(axis=1,name='batch_008'))
    model.add(Activation('relu',name='relu_009'))
    model.add(Conv2D(64, (3, 3),name='convo2D_010'))
    model.add(BatchNormalization(axis=1,name='batch_011'))
    model.add(Activation('relu',name='relu_012'))
    model.add(MaxPooling2D(pool_size=(2, 2),name='pool_013'))

    model.add(Conv2D(128, (3, 3), padding='same',name='convo2D_014'))
    model.add(BatchNormalization(axis=1,name='batch_015'))
    model.add(Activation('relu',name='relu_016'))
    model.add(Conv2D(128, (3, 3),name='convo2D_017'))
    model.add(BatchNormalization(axis=1,name='batch_018'))
    model.add(Activation('relu',name='relu_019'))
    model.add(MaxPooling2D(pool_size=(2, 2),name='pool_020'))

    model.add(Flatten(name='flat_021'))
    model.add(Dense(512,name='dense_022'))
    model.add(BatchNormalization(axis=1,name='batch_0023'))
    model.add(Activation('relu',name='relu_024'))
    model.add(Dense(nb_classes,name='dense_025'))
    model.add(Activation('softmax',name='soft_026'))

    model.compile(loss='categorical_crossentropy', optimizer='nadam', metrics=['accuracy'])
    print(model.summary())

    return model


def getDNN(nb_classes=8,nb_slices=30):

    # Define tihe model architecture: layers, parameters, etc...
    # nb_classes=8, is the number of MRI contrasts the algorithm will attempt to model
    # nb_slices=30, is the number of sagittal slices CNN was used to make an initial inference
    # This network combined the CNN-inference generated on 30 slices to one volumetric inference

    model = Sequential()

    model.add(Dense(64,input_dim=nb_slices*nb_classes))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dense(nb_classes))
    model.add(Activation('softmax'))

    model.compile(loss='categorical_crossentropy',optimizer='nadam',metrics=['accuracy'])
    print(model.summary())

    return model


# input_size: dimension of sagittal slice
input_size=(1,32,32)
# nb_classes: number of MRI contrasts the algorithm attempts to infer
nb_classes = [5,8]
# nb_slices: number of sagittal slices used to represent the MRI volume
nb_slices = 30
# networks: a convolutional neural network (CNN) and dense neural network (DNN) used to infer the MRI contrast
networks = ['CNN','DNN']

for n in nb_classes:
    for NN in networks:
        if 'DNN' in NN:
            model = getDNN(n,nb_slices)
        else:
            model = getCNN(n,input_size)
        # save NN as JSON string
        json_string = model.to_json()
        fn = "./model/{0}_{1}mod.json".format(NN,n)
        print("Saving %s" % fn)
        with open(fn, 'w') as outfile:
            json.dump(json_string, outfile)


