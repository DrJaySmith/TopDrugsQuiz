from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configure Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

try:
    # Navigate to lecture URL
    driver.get("https://leccap.engin.umich.edu/leccap/player/r/eygmQB")

    # Wait for Weblogin redirect and handle JavaScript requirements
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "login"))
    )

    # Fill UMich credentials
    username = driver.find_element(By.ID, "smithjay")
    password = driver.find_element(By.ID, "5Drneqrk(&*)CHN")

    username.send_keys("smithjay")  # Replace with actual credentials
    password.send_keys("5Drneqrk(&*)CHN")  # Replace with actual password

    # Submit form
    driver.find_element(By.NAME, "_eventId_proceed").click()

    # Manual Duo 2FA Handling
    print("Complete Duo 2FA authentication in the browser...")
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CLASS_NAME, "transcript-row"))
    )

    # Extract transcript after successful authentication
    transcript_rows = driver.find_elements(By.CLASS_NAME, "transcript-row")

    with open("transcript.txt", "w", encoding="utf-8") as f:
        for row in transcript_rows:
            time_element = row.find_element(By.CLASS_NAME, "transcript-time")
            text_element = row.find_element(By.CLASS_NAME, "transcript-text").find_element(By.TAG_NAME, "span")
            f.write(f"{time_element.text}: {text_element.text}\n")

    print("Transcript successfully saved to transcript.txt")

finally:
    driver.quit()