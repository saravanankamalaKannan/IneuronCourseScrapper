import logging
log_file="ineuronScrapper.log"
log_instance="ineuron"

logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(log_instance)