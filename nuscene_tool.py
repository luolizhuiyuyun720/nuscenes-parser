import os
import sys
import json
import shutil

sample_data = {}        #token as key
ego_pose = {}           #token as key
calibrated_sensor = {}  #token as key   
scene = {}              #token as key
sample = {}             #token as key 
cloud_files={}          #timestamp as key
poses={}                #timestamp as key, listed [sensor2ego,ego2worl]

def decoratorLoad(fn):
  def printLog(*args):
    print("Load", *args, "...", end="")
    fn(*args)
    print("finish!")
  return printLog

def loadJson(filepath, key):
  with open(filepath, 'r') as fin:
    json_obj=json.load(fin)
  json_dict={}
  for elem in json_obj:
    key_str = elem.get(key)
    if None !=  key_str:
      json_dict[key_str]=elem
  
  return json_dict

@decoratorLoad
def loadSampleData(json_file):
  global sample_data
  sample_data=loadJson(json_file, "token")

@decoratorLoad
def loadEgoPose(json_file):
  global ego_pose
  ego_pose=loadJson(json_file, "token")

@decoratorLoad
def loadCalibrationSensor(json_file):
  global calibrated_sensor
  calibrated_sensor=loadJson(json_file, "token")  

@decoratorLoad
def loadScene(json_file):
  global scene
  scene=loadJson(json_file, "token")

@decoratorLoad
def loadSample(json_file):
  global sample
  sample=loadJson(json_file, "token")

##########################################################
# load nuscene data
##########################################################
def loadDataSets(folder_path):
  file_list = os.listdir(folder_path)
  funs = {
    "ego_pose.json" : loadEgoPose,
    "sample_data.json" : loadSampleData,
    "sample.json" : loadSample,
    "scene.json" : loadScene,
    "calibrated_sensor.json" : loadCalibrationSensor
  }
  for file_name in file_list:  
    method = funs.get(file_name)
    if None != method:
      file_path = folder_path + "/" + file_name
      method(file_path)

def loadCloudFiles(cloud_folder):
  file_list = os.listdir(cloud_folder)
  file_list.sort()
  frame_count = 0 
  global cloud_files
  for file_name in file_list:
    substr=file_name.split("__")
    ts=substr[-1].split(".")[0]
    cloud_files[ts]=cloud_folder+"/"+file_name

############################################################
# find related pose from LIDAR_TOP cloud file timestamp
############################################################
def findSampleToken(ts):
  global sample_data
  for key in sample_data:
    obj = sample_data[key]
    if str(obj["timestamp"]) == ts:
      return obj["ego_pose_token"], obj["calibrated_sensor_token"]
  return None

def findEgoPose(token):
  global ego_pose
  elem = ego_pose.get(token)
  if None != elem:
    l = []
    l.extend(elem["translation"])
    l.extend(elem["rotation"])
    return l
  return None

def findCalibrationPose(token):
  global calibrated_sensor  
  elem =calibrated_sensor.get(token)
  if None != elem:
    l = []
    l.extend(elem["translation"])
    l.extend(elem["rotation"])
    return l
  return None
      
def findCloudPose(ts):
  global poses
  poses[ts]=[]
  ego_pose_token, cali_sensor_token = findSampleToken(ts)
  if None != ego_pose_token:
    ego2world = findEgoPose(ego_pose_token)
    if None != ego2world:
      poses[ts].append(ego2world)
  if None != cali_sensor_token:
    sensor2ego = findCalibrationPose(cali_sensor_token)
    if None != sensor2ego:
      poses[ts].append(sensor2ego)
  
###########################################################
# write
###########################################################
def decoratorPath(fn):
  def printLog(*args):
    print("Create Path", *args, "...", end="")
    fn(*args)
    print("finish!")
  return printLog

@decoratorPath
def checkFolder(folder):
  if not os.path.exists(folder):
    os.makedirs(folder)
  
def checkOutputFolder(out_folder):
  cloud_folder= out_folder+"/cloud/"
  ego2world_folder = out_folder+"/ego2world/"
  sensor2ego_folder = out_folder+"/sensor2ego/"
  checkFolder(cloud_folder)
  checkFolder(ego2world_folder)
  checkFolder(sensor2ego_folder)
  return cloud_folder, ego2world_folder, sensor2ego_folder

def writePoseFile(file_path, frame_count, ts, pose):
  f = open(file_path, "w")
  s = str(int(frame_count)); s += '\t'
  s += str(ts); s+= '\t'
  for value in pose:
    s += str(round(value,6)); s+= '\t'
  f.write(s)
  f.close()

def export2Apollo(output_folder):
  cloud_path, ego2world_path, sensor2ego_path = \
    checkOutputFolder(output_folder)
  
  global cloud_files
  global poses
  frame_count=0
  for key in cloud_files:
    ts=str(key)
    findCloudPose(ts)
    file_name = "cloud_"+str(frame_count).zfill(8)+".bin"
    src_path = cloud_files[key]
    cloud_dst_path = cloud_path+"/"+file_name
    shutil.copyfile(src_path, cloud_dst_path)
    list_of_pose = poses.get(key)
    if None != list_of_pose:
      ego2world_dst_path = ego2world_path+"/"+file_name+".pose"
      sensor2ego_dst_path = sensor2ego_path+"/"+file_name+".pose"
      writePoseFile(ego2world_dst_path, frame_count, key, list_of_pose[0])
      writePoseFile(sensor2ego_dst_path, frame_count, key, list_of_pose[1])
    frame_count += 1

############################################################
# main
############################################################
def main(argv):
  loadDataSets(argv[2])
  global ego_pose
  print("ego_pose len", len(ego_pose))
  print("calibrated_sensor len: ", len(calibrated_sensor))
  print("sample_data len", len(sample_data))
  print("sample len", len(sample))
  print("scene len", len(scene))
  loadCloudFiles(argv[1])
  print("cloud file len:", len(cloud_files))
  export2Apollo(argv[3])
  print("poses len", len(poses))

if __name__ == "__main__":
  main(sys.argv)

