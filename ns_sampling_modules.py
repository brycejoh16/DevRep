import pandas as pd
import numpy as np
import tensorflow as tf
import os
import sys
import ns_plot_modules as pm
tf.config.optimizer.set_jit(True)

def incorrect_blanks(random_AA, random_AA_pos, seq):
    '''
    :param random_AA: Nx1 ndarray of suggested AA to change to
    :param random_AA_pos: Nx1 ndarray of random Amino acid positions
    :param seq:Nx16 ndarray current sequences before mutations
    :return: logical, where true means an invalid sample
    '''

    # make sure that its in position 3,4,11,12
    # and if its in position 4,
    # make sure 3 is 19 otherwise resample
    # and if its in position 12,
    # make sure 11 is 19 otherwise resample
    out_of_bounds_regoin = np.bitwise_and(random_AA == 19,
                                          np.bitwise_and(
                                              np.bitwise_and(random_AA_pos != 4, random_AA_pos != 3),
                                              np.bitwise_and(random_AA_pos != 11, random_AA_pos != 12)
                                          ))
    # if the AA at position 3/11 wants to change to AA 19, then make sure that AA at position 4/12 is 19
    invalid_blank_regoin = np.bitwise_and(random_AA == 19,
                                          np.bitwise_or(
                                              np.bitwise_and(random_AA_pos == 3, seq[:, 4] != 19),
                                              np.bitwise_and(random_AA_pos == 11, seq[:, 12] != 19)
                                          ))
    # if the AA at position 4/12 wants to change to something other than 19 and 3/11 is currently 19,
    # then that is an invalid move
    invalid_change_back = np.bitwise_and(random_AA != 19,
                                         np.bitwise_or(
                                             np.bitwise_and(random_AA_pos == 4, seq[:, 3] == 19),
                                             np.bitwise_and(random_AA_pos == 12, seq[:, 11] == 19)
                                         ))

    change_blanks = np.bitwise_or(np.bitwise_or(out_of_bounds_regoin, invalid_blank_regoin), invalid_change_back)
    return change_blanks


def remove_blanks(random_AA_pos, random_AA, seq, generator):
    'removes sequences which are out of sequence space'
    # seq is a numpy 2D array of ordinals.
    # random_AA_pos is the random position of Amino acids: this does not change in these functions
    # random_AA is random AA to change to.

    change_blanks = incorrect_blanks(random_AA=random_AA, random_AA_pos=random_AA_pos, seq=seq)
    size=[-1]
    while change_blanks.any():
        size.append(np.count_nonzero(change_blanks))
        # print('change these blanks %i' % size[-1])
        random_AA[change_blanks] = sample(nb_of_sequences= size[-1],Nb_positions= 0, generator=generator)
        change_blanks = incorrect_blanks(random_AA=random_AA, random_AA_pos=random_AA_pos, seq=seq)
    return random_AA


def convert2pandas(ordinals_np):
    '''
    :param ordinals_np: numpy array to transition to pandas column
    :return: pandas wierd format
    '''
    ord_pd = []
    # make a list of tuples
    for i in ordinals_np:
        ord_pd.append((i))
    return ord_pd


def convert2numpy(df, field='Ordinal'):
    '''
    :param df: pandas dataframe
    :param field: column to transmit to numpy array
    :return: returns numpy array
    '''
    return np.copy(np.array(df[field].to_numpy().tolist()))
def splitPandas(df,nb_splits=10):
    '''

    :param df: dataframe to split
    :param nb_splits: number of splits to do to dataset for parrelel processing
    :return: list of dataframes

    '''
    field='Ordinal'
    seq=convert2numpy(df=df,field=field)
    lst=np.array_split(seq,indices_or_sections=nb_splits,axis=0)
    return list(map(pandas_dataframe,lst))

def pandas_dataframe(seq):
    a=pd.DataFrame()
    a['Ordinal']=convert2pandas(ordinals_np=seq)
    return a

def sample(nb_of_sequences, Nb_positions, generator,minval=0,maxval=21):
    'if nb_positions is 0 then will '
    if Nb_positions is 0:
        return generator.uniform(shape=[nb_of_sequences], minval=minval, maxval=maxval, dtype=tf.int64).numpy()
    return generator.uniform(shape=[nb_of_sequences, Nb_positions], minval=minval, maxval=maxval, dtype=tf.int64).numpy()
    # have two generators

def make_sampling_data_force(generator,force=None,Nb_sequences=100,Nb_positions=16):
    '''
    note this function only works when initially sampling data not correcting for mutations, etc.
    :param generator: tensorflow generator to generator random data
    :param force:  a dictionary showing what positions to force with which amino acids
    :param Nb_sequences:
    :return:
    '''
    if bool(force) is False:
        return make_sampling_data(generator=generator,Nb_sequences=Nb_sequences,Nb_positions=Nb_positions)
    df=pd.DataFrame()
    cpos=1
    if force is None:
        force={'7':cpos,'6':cpos,'36':cpos}

    P=convert_labels_2_ordinal(force)
    p=convert2numpy(df=P,field='ordinal')
    seq = sample(nb_of_sequences=Nb_sequences, Nb_positions=Nb_positions, generator=generator)
    for k in np.arange(Nb_positions):
        # at the kth position in every sequence

        if k not in p:
            seq[:, k] = remove_blanks(random_AA_pos=np.ones((Nb_sequences)) * k, random_AA=seq[:, k].copy(), seq=seq,
                                  generator=generator)
        else:
            idx=np.argmax(p==k)
            AA=convert2numpy(df=P, field='AA')
            seq[:,k]= AA[idx]


    return convert2pandas(seq)





def convert_labels_2_ordinal(force):
    '''
    :param force: a dictionary showing what positions to force with which amino acids
    :return:a dataframe with columns key , ordinal , and AA, which is the forced amino acid
    '''
    labels = np.array(
        ['7', '8', '9', '9b', '9c', '10', '11', '12', '34', '35', '36', '36b', '36c', '37', '38', '39', 'Loop 1 (8-11)',
         'Loop 2 (34-39)', 'Loop 1 & Loop 2'])
    P = pd.DataFrame()
    for k,j in zip(force.keys(),range(len(force))):
        P.loc[j,'key']=k
        P.loc[j,'ordinal']=np.argmax(labels == k)
        P.loc[j,'AA']=force[k]
    return P

def make_sampling_data(generator, Nb_sequences=1000, Nb_positions=16):
    '''
    make sampling data and then remove all the illegal blanks
    :param generator: tensorflow.random.experimental generator from v2.0
    :param Nb_sequences: specify number of sequences
    :param Nb_positions: specifies number of positions
    :return: return ordinals in pandas format

    '''
    seq = sample(nb_of_sequences=Nb_sequences, Nb_positions=Nb_positions, generator=generator)
    for k in np.arange(Nb_positions):
        # at the kth position in every sequence
        seq[:, k] = remove_blanks(random_AA_pos=np.ones((Nb_sequences)) * k, random_AA=seq[:, k].copy(), seq=seq,
                                  generator=generator)
    return convert2pandas(seq)


def _unit_tests_accuracy_blank_removal():
    'this is a unit test for removal of blanks, not for actual usage. Not to be implemented.'
    seed_parent = int.from_bytes(os.urandom(4), sys.byteorder)
    g_parent = tf.random.experimental.Generator.from_seed(seed_parent)
    seq = np.array([[0, 0, 0, 19, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 19, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
    random_AA = np.array([4, 19])
    random_AA_pos = np.array([4, 12])
    remove_blanks(random_AA=random_AA, random_AA_pos=random_AA_pos, seq=seq, generator=g_parent)



