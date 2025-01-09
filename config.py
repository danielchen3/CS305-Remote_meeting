HELP = 'Create         : create an conference\n' \
       'Join [conf_id ]: join a conference with conference ID\n' \
       'Quit           : quit an on-going conference\n' \
       'Cancel         : cancel your on-going conference (only the manager)\n\n'

# Please fill in using the server IP
SERVER_IP = ''
# Please fill in using your own IP
P2P_own_IP = ''
MAIN_SERVER_PORT = 8888
TIMEOUT_SERVER = 5
# DGRAM_SIZE = 1500  # UDP
LOG_INTERVAL = 2

CHUNK = 5120
CHANNELS = 2  # Channels for audio capture
RATE = 48000  # Sampling rate for audio capture

camera_width, camera_height = 480, 480  # resolution for camera capture
