import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def get_logger() -> logging.Logger:
    return logger

if __name__ == "__main__":
    get_logger().info("Application started")
    get_logger().warning("Something looks wrong")
    get_logger().error("Something failed")