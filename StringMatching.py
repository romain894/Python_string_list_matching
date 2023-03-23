# Romain THOMAS 2023
# Stockholm Resilience Centre, Stockholm University

from tqdm import tqdm # progress bar
from multiprocessing import Pool, Lock, Value # multiprocessing to increase execution speed
from difflib import SequenceMatcher # To match similar strings
import numpy as np # To manage arrays
import time
import datetime # to display loading time
import humanize # to display nicely the time
from os.path import exists # To check if a file exist

class StringMatching():
    """!
    @brief      A Python class to match similar strings
                based on SequenceMatcher from difflib
    """
    def __init__(self, string_names, nb_string_names):
        self.string_names = string_names
        self.nb_string_names = nb_string_names
        self.ratio_array = None
        self.link_strings_list = None
        self.string_names_linked = None

    def init_pool_processes(self, lock_1, lock_2, shared_counter):
        """!
        Initialize each process with global variable locks and counter (for
        the multiprocessing)
        
        @param      lock_1          The lock for the print display (lock)
        @param      lock_2          The lock for the counter (lock)
        @param      shared_counter  The shared counter to calculate the
                                    remaining computation time (Value)
        """
        global display_lock
        display_lock = lock_1
        global count_eta_lock
        count_eta_lock = lock_2
        global ratios_computed
        ratios_computed = shared_counter


    def compute_ratio_strings(self, i):
        """!
        Compute the ratios for an string, used for the multiprocessing of
        compute_ratio_array_strings()
        
        @param      i     id of the string to compute the ratio to (int)
        
        @return     The ratio string list. (int[])
        """
        tmp_string_names = [None] * (i + 1)
        for j in range(i + 1):
            if self.string_names[i] != None and self.string_names[j] != None:
                tmp_string_names[j] = SequenceMatcher(None, self.string_names[i], self.string_names[j]).ratio()
            else:
                tmp_string_names[j] = None
        # add the computation progress done
        count_eta_lock.acquire()
        ratios_computed.value = ratios_computed.value + i + 1
        count_eta_lock.release()
        if i%50 == 0:
            display_lock.acquire()
            ratio_percentage_computed = ratios_computed.value / self.total_ratios_to_compute * 100
            elapsed_time = datetime.datetime.now() - self.time_computation_start
            remaining_time = None
            if(ratio_percentage_computed != 0):
                remaining_time = elapsed_time * (100 - ratio_percentage_computed) / ratio_percentage_computed
            else:
                remaining_time = 9999
            # keep printing on the same line
            remaining_time_str = humanize.precisedelta(remaining_time, minimum_unit="seconds", format="%0.0f")
            print("Computing string ratios: "+str(round(ratio_percentage_computed, 2))+" % ("+remaining_time_str+")                      ", end="\r")
            #print(i)
            display_lock.release()
        return tmp_string_names

    def compute_ratio_array_strings(self, ratio_array_csv_path = None, use_cache = True, cache_ratio_array_path = None, max_process_nb = 8):
        """!
        @brief      Calculates the strings ratio array.

        @param      ratio_array_csv_path    The ratio array csv path to save it (if not provided, it won't be saved) (string)
        @param      use_cache               The use cache (indicate if we use the cache, aka load the cache if existing)
        @param      cache_ratio_array_path  The cache ratio array path where it's loaded or saved (string)
        @param      max_process_nb          The maximum number of process (minimum 1) (int)
        """
        # check if there is a cache file (precalculated) and if we should use it:
        need_to_compute = True # True if we need to compute again
        if use_cache == True:
            if cache_ratio_array_path == None:
                print("No cache ratio file provided for compute_ratio_array but use_cache = True, can't load the cache")
            else:
                # if the file doesn't exist
                if not exists(cache_ratio_array_path):
                    print("Cache file not found")
                else:
                    print("Loading the cache from file...")
                    data = np.load(cache_ratio_array_path, allow_pickle=True)
                    if list(data['titles_without_id_cached']) == self.string_names:
                        print("Cache match the current computation, no need to compute again")
                        # the ratio_array is stored as a numpy array of lists, so we need to convert it as
                        # a list to get a list of lists
                        self.ratio_array = list(data['ratio_array_cached'])
                        need_to_compute = False
                    else:
                        print("Cache found but doesn't match the current computation, need to compute again")
        else:
            print("Cache usage disabled")
        
        if need_to_compute == True:
            #max_process_nb = 1 # help to debug, it print in the right order
            max_id_computation = self.nb_string_names
            #max_id_computation = 2000 # avoid to compute everything, for developpment proposes
            display_lock = Lock() # the usage of the lock if optional, only for a cleaner print
            count_eta_lock = Lock() # the usage of the lock if optional, only for progress visualisation
            if max_id_computation == self.nb_string_names:
                print("computing all the references match ratios...")
            else:
                print("computing the", max_id_computation, "first references match ratios")
            # define a partial function to call compute_ratio() with a prefilled argument each time
            # here the prefilled argument will be self.string_names
            # compute_ratio_with_list = partial(compute_ratio, self.string_names) # not used anymore
            # as a the function compute_ratio_titles is only for titles
            t_start = time.time()
            self.time_computation_start = datetime.datetime.now()
            self.total_ratios_to_compute = max_id_computation * max_id_computation / 2 + max_id_computation / 2
            ratios_computed = Value('i', 0)
            with Pool(processes = max_process_nb, initializer = self.init_pool_processes, initargs = (display_lock, count_eta_lock, ratios_computed)) as p:
                self.ratio_array = p.map(self.compute_ratio_strings, range(max_id_computation))
            t_end = time.time()
            t = t_end - t_start
            print("Computation time: ", round(t, 2), "s")
            # Calculate the expected computation time for max_id_computation = self.nb_string_names
            t_expected = t * (self.nb_string_names*self.nb_string_names) / (max_id_computation*max_id_computation)
            print("Computation time expected for the whole array: ", round(t_expected, 2), "s")

            # Save in cache the array if we want to use the cache and we computed the whole ratio array
            if use_cache == True and max_id_computation == self.nb_string_names:
                if cache_ratio_array_path == None:
                    print("No cache ratio file provided for compute_ratio_array but use_cache = True, can't save the cache")
                else:
                    # Save the ratio array in cache (self.string_names is saved to control that the cache match with the actual list):
                    # We need to create a numpy array of objects to store self.string_names because it's not a numpy array
                    print("Saving ratio array in cache...")
                    np_string_names = np.array(self.string_names, dtype=object)
                    np.savez_compressed(cache_ratio_array_path, ratio_array_cached=self.ratio_array, titles_without_id_cached=np_string_names)
                    print("Ratio array saved in cache")

        # Save as CSV if file provided
        if ratio_array_csv_path != None:
            print("Saving the ratio array as CSV...")
            # Convert ratio to a dataframe to save as CSV file
            df_ratio_array = pd.DataFrame(data=self.ratio_array)
            # save the dataframe to csv (to explore the datas and import later)
            df_ratio_array.to_csv(ratio_array_csv_path)
            print("Ratio array dataframe saved in", ratio_array_csv_path)


    def link_strings_from_ratios_array(self, string_link_ratio_threshold, string_link_ratio_warning):
        """!
        @brief      Links the strings. To run after that the ratio array is computed or loaded from the cache
        
        @param      string_link_ratio_threshold  The reference link ratio
                                              threshold (fload from 0 to 1)
        @param      ref_link_ratio_warning    The reference link ratio
                                              warning (float from 0 to 1)
        """
        # will contain the similar strings identified by their position
        self.link_strings_list = [None] * len(self.ratio_array)
        for i in range(len(self.ratio_array)):
            self.link_strings_list[i] = [i]
        # for each ration computed, except the ones from the diagonal
        for i, ratio_array_row in enumerate(self.ratio_array):
            nb_link_in_ratio_row = 0
            position_of_the_first_row_link = None
            for j, ratio in enumerate(ratio_array_row[0:-1]):
                if ratio > string_link_ratio_threshold:
                    nb_link_in_ratio_row += 1
                    # we move the identifier to the list of the one which matches
                    self.link_strings_list[i] = [-1]
                    # we check if the identifier matched is still at his original place
                    if self.link_strings_list[j] != [-1]:
                        # this is the first link in the ratio row
                        if nb_link_in_ratio_row == 1:
                            position_of_the_first_ratio_row_link = j
                            # check if the identifier is not already in the list:
                            if self.link_strings_list[j].count(i) == 0:
                                # we append the identifier i to the list of the identifier j
                                self.link_strings_list[j].append(i)
                        # there is already a link in the row, so we need to merge the destination row in the row where i was previously added
                        else:
                            for j_item in self.link_strings_list[j]:
                                self.link_strings_list[position_of_the_first_ratio_row_link].append(j_item)
                            self.link_strings_list[j] = [-1] # we erase the merged line as it's now in self.link_strings_list[position_of_the_first_ratio_row_link]
                    # the identifier j has already been moved
                    else:
                        # we look for the identifier j:
                        k = 0 # we start to search at k = 0
                        while self.link_strings_list[k].count(j) == 0:
                            k += 1
                        # this is the first link in the ratio row
                        if nb_link_in_ratio_row == 1:
                            position_of_the_first_ratio_row_link = k
                            # check if the identifier is not already in the list:
                            if self.link_strings_list[k].count(i) == 0:
                                # we append the identifier i to the list of the identifier k (which contains the identifier j)
                                self.link_strings_list[k].append(i)
                        # there is already a link in the row, so we need to merge the destination row and the row where i was previously added
                        else:
                            # check if the identifier is not already in the list:
                            if self.link_strings_list[k].count(j) == 0:
                                # we append the identifier j to the list of the identifier k (which contains the identifier i)
                                self.link_strings_list[k].append(j)
        #for sub_list in self.link_strings_list:
        #    print(sub_list)
        # Remove the -1 elements
        self.link_strings_list = [item for item in self.link_strings_list if item != [-1]]

    def create_ref_citation_id_link(self):
        """!
        Create an array which gives the matches/links between the similar
        strings, like link_strings_list() but use the
        name of the strings instead of the ratio_array_id to identify each
        string (it gives a list with each sub lists containing the
        strings names of all the identical strings)
        
        @return     The list of list with similar strings, identified with their names (str[][])
        """
        if self.link_strings_list == -1:
            raise ValueError("The links between strings were not calculated before, cannot continue the execution")
        self.string_names_linked = [None] * len(self.link_strings_list)            
        for i, strings in enumerate(self.link_strings_list):
            self.string_names_linked[i] = [None] * len(strings)
            for j, j_string in enumerate(strings):
                self.string_names_linked[i][j] = self.string_names[j_string]

    def sort_string_names_linked_list(self):
        """!
        @brief      Sort the list self.string_names_linked by the len of each element
        """
        self.string_names_linked = sorted(self.string_names_linked, key=len, reverse=True)

    def link_strings(self,  link_ratio_threshold = 0.85,
                            link_ratio_warning = 0,
                            cache_ratio_array_path = None,
                            use_cache = True,
                            ratio_array_csv_path = None,
                            sort_linked_list_by_len = True):

        self.compute_ratio_array_strings(ratio_array_csv_path, use_cache, cache_ratio_array_path)

        self.link_strings_from_ratios_array(link_ratio_threshold, link_ratio_warning)

        self.create_ref_citation_id_link()

        if sort_linked_list_by_len:
            self.sort_string_names_linked_list()

        return self.string_names_linked