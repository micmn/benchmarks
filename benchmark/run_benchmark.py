'''
  @file run_benchmark.py
  @author Marcus Edel

  Perform the timing benchmark.
'''

import os, sys, inspect

# Import the util path, this method even works if the path contains
# symlinks to modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], '../util')))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from log import *
from system import *
from loader import * 
from parser import *
from convert import *

import argparse

'''
Show system informations. Are there no data available, the value is 'N/A'.
'''
def SystemInformation():
  
  Log.Info('CPU Model: ' + SystemInfo.GetCPUModel())
  Log.Info('Distribution: ' + SystemInfo.GetDistribution())
  Log.Info('Platform: ' + SystemInfo.GetPlatform())
  Log.Info('Memory: ' + SystemInfo.GetMemory())
  Log.Info('CPU Cores: ' + SystemInfo.GetCPUCores())

'''
Normalize the dataset name. If the dataset is a list of datasets, take the first
dataset as name. If necessary remove characters like '.', '_'.

@param dataset - Dataset file or a list of datasets files.
@return Normalized dataset name.
'''
def NormalizeDatasetName(dataset):
  if not isinstance(dataset, str):
    return os.path.splitext(os.path.basename(dataset[0]))[0].split('_')[0]
  else:
    return os.path.splitext(os.path.basename(dataset))[0].split('_')[0]

'''
Check if the file is available in one of the given formats.

@param dataset - Datsets which should be checked.
@param formats - List of supported file formats.
@return Orginal dataset or dataset with new file format.
'''
def CheckFileExtension(dataset, formats):
  dataExtension = os.path.splitext(dataset)[1][1:]
  if dataExtension in formats:
    return dataset
  else:
    return dataset[0:len(dataset) - len(dataExtension)] + formats[0]

'''
Return a list with modified dataset.

@param dataset - Datasets to be modified.
@param format - List of file formats to be converted to.
@return List of modified datasets.
'''
def GetDataset(dataset, format):
  # Check if the given dataset is a list or a single dataset.
  if not isinstance(dataset, str):
    datasetList = []
    modifiedList = []

    for data in dataset:  
      mdata = CheckFileExtension(data, format)

      # Check if the dataset is available.
      if os.path.isfile(mdata):
        datasetList.append(mdata)
      else:
        # Check if the dataset is available.
        convert = Convert(data, format[0])
        datasetList.append(convert.modifiedDataset)
        modifiedList.append(convert.modifiedDataset)
  else:
    datasetList = ""
    modifiedList = ""

    mdataset = CheckFileExtension(dataset, format)

    # Check if the dataset is available.
    if os.path.isfile(mdataset):
      datasetList = mdataset
    else:
      # Convert the Dataset.
      convert = Convert(dataset, format[0])
      datasetList = convert.modifiedDataset
      modifiedList = convert.modifiedDataset

  return (datasetList, modifiedList)

'''
This function Remove a given file or list of files.

@param dataset - File or list of file which should be deleted.
'''
def RemoveDataset(dataset):
  if isinstance(dataset, str):
    dataset = [dataset]

  for f in dataset:
    if os.path.isfile(f):
      os.remove(f)  

'''
Add all rows from a given matrix to a given table.

@param matrix - 2D array contains the row.
@param table - Table in which the rows are inserted.
@return Table with the inserted rows.
'''
def AddMatrixToTable(matrix, table):
  for row in matrix:
    table.append(row)
  return table

'''
Count all datasets to determine the dataset size.

@param libraries - Contains the Dataset List.
@return Dataset count.
'''
def CountLibrariesDatasets(libraries):
  datasetList = []
  for libary in libraries:
    for dataset in libary[1]:
      name = NormalizeDatasetName(dataset)
      if not name in datasetList:
        datasetList.append(name)

  return len(datasetList)

'''
Search the correct row to insert the new data. We look at the left column for
a free place or for the matching name.

@param dataMatrix - In this Matrix we search for the right position.
@param datasetName - Name of the dataset.
@param datasetCount - Maximum dataset count.
'''
def FindRightRow(dataMatrix, datasetName, datasetCount):
  for row in range(datasetCount):
    if (dataMatrix[row][0] == datasetName) or (dataMatrix[row][0] == "-"):
      return row

'''
Start the main benchmark routine. The method shows some DEBUG information and 
prints a table with the runtime information.

@para configfile - Start the benchmark with this configuration file.
'''
def Main(configfile):
  # Benchmark settings.
  timeout = 23000

  # Read Config.
  config = Parser(configfile, verbose=False)
  streamData = config.StreamMerge()

  # Read the general block and set the attributes.
  if "general" in streamData:
    for key, value in streamData["general"]:
      if key == "timeout":
        timeout = value
      elif key == "MLPACK_BIN":
        os.environ["MLPACK_BIN"] = value
      elif key == "MATLAB_BIN":
        os.environ["MATLAB_BIN"] = value
      elif key == "MATLABPATH":
        os.environ["MATLABPATH"] = value
      elif key == "PYTHONPATH":
        try:
          PYTHONPATH = os.environ["PYTHONPATH"]
        except KeyError:
          os.environ["PYTHONPATH"] = value
        else:
          os.environ["PYTHONPATH"] = PYTHONPATH + ":" + value
      elif key == "LD_LIBRARY_PATH":
        try:
          LD_LIBRARY_PATH = os.environ["LD_LIBRARY_PATH"]
        except KeyError:
          os.environ["LD_LIBRARY_PATH"] = value
        else:
          os.environ["LD_LIBRARY_PATH"] = LD_LIBRARY_PATH + ":" + value


  # Iterate through all libraries.
  for method, sets in streamData.items():
    if method == "general":
      continue
    Log.Info("Method: " + method)    
    for options, libraries in sets.items():
      Log.Info('Options: ' + (options if options != '' else 'None'))

      # Create the Table.
      table = []
      header = ['']
      table.append(header)

      # Count the Datasets.
      datasetCount = CountLibrariesDatasets(libraries)

      # Create the matrix which contains the time and dataset informations.
      dataMatrix = [['-' for x in range(len(libraries) + 1)] for x in 
          range(datasetCount)] 

      col = 1
      for libary in libraries:
        name = libary[0]
        datsets = libary[1]
        trials = libary[2]
        script = libary[3]
        format = libary[4]

        Log.Info("Libary: " + name)
        header.append(name)

        # Load script.
        try:
          module = Loader.ImportModuleFromPath(script)
          methodCall = getattr(module, method)
        except Exception as e:
          Log.Fatal("Could not load the script: " + script)
          Log.Fatal("Exception: " + str(e))
          continue

        for dataset in datsets:  
          datasetName = NormalizeDatasetName(dataset)          
          row = FindRightRow(dataMatrix, datasetName, datasetCount)      

          dataMatrix[row][0] = NormalizeDatasetName(dataset)
          Log.Info("Dataset: " + dataMatrix[row][0])    

          modifiedDataset = GetDataset(dataset, format)

          try:
            instance = methodCall(modifiedDataset[0], timeout=timeout, verbose=False)
          except Exception as e:
            Log.Fatal("Could not call the constructor: " + script)
            Log.Fatal("Exception: " + str(e))
            continue

          time = 0
          for trial in range(trials + 1):
            if trial > 0:
              try:
                time += instance.RunMethod(options);

                # Method unsuccessful.
                if time < 0:
                  break
              except Exception as e:
                Log.Fatal("Exception: " + str(e))

          # Set time.
          if time == -2:
            dataMatrix[row][col] = ">" + str(timeout)
          else:
            dataMatrix[row][col] = "{0:.6f}".format(time / trials)

          # Remove temporary datasets.
          RemoveDataset(modifiedDataset[1])
          row += 1
        col += 1

      # Show results in a table.
      Log.Notice("\n\n")
      Log.PrintTable(AddMatrixToTable(dataMatrix, table))
      Log.Notice("\n\n")

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="""Perform the benchmark with the
      given config.""")
  parser.add_argument('-c','--config', help='Configuration file name.', 
      required=True)

  args = parser.parse_args()

  if args:
    SystemInformation()
    Main(args.config)
