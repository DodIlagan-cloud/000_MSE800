#W2A1_wordguessgame
import random as rdm
import numpy as np 

def gen_word ():
    word_list = ["braveheart","hugo","nosferatu","interstellar","kingdom","annihilation","speed"]
    guess_word = rdm.choice(word_list)
    return guess_word

def gen_blank ():
    word_blank_arr =np.empty(shape=g_word_size,dtype='<U1')
    return word_blank_arr

def play ():
    trial = 0
    while trial > 3:
        guess_letter = input()
        trial ++

if __name__ == "__main__":
    g_guess_word=gen_word()
    g_word_size = len(g_guess_word)
    print(f"{g_guess_word},{g_word_size}")
    print(f"Guess the random word, it has {g_word_size} letters.")
    blanks_arr=gen_blank()
    #blanks_arr=[_]
    print(blanks_arr)


    g_guess_letter = input()