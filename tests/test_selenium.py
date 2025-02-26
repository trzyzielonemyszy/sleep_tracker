from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from datetime import datetime, timedelta
import pytest
import pytz
import time
import os

@pytest.fixture
def driver():
    # Setup Edge driver with headless option
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
        yield driver
    finally:
        if 'driver' in locals():
            driver.quit()

def test_homepage_loads(driver):
    driver.get("http://localhost:5000")  # Adjust URL as needed
    assert "Chat Application" in driver.title

def test_message_timestamps(driver):
    driver.get("http://localhost:5000")
    
    # Wait for messages to load
    messages = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "message-timestamp"))
    )
    
    # Check if timestamps are present and in correct format
    for timestamp_element in messages:
        timestamp_text = timestamp_element.text
        try:
            # Try to parse the timestamp (adjust format as needed)
            datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            pytest.fail(f"Invalid timestamp format: {timestamp_text}")

def test_timezone_consistency(driver):
    driver.get("http://localhost:5000")
    
    # Get local timezone
    local_tz = datetime.now().astimezone().tzinfo
    
    # Wait for and get timestamps
    timestamps = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "message-timestamp"))
    )
    
    for timestamp_element in timestamps:
        timestamp_text = timestamp_element.text
        try:
            # Parse the timestamp and check timezone
            dt = datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
            dt = pytz.UTC.localize(dt).astimezone(local_tz)
            
            # Verify the displayed time matches the expected local time
            expected_display = dt.strftime("%Y-%m-%d %H:%M:%S")
            assert timestamp_text == expected_display, \
                f"Timestamp timezone mismatch. Expected: {expected_display}, Got: {timestamp_text}"
                
        except ValueError as e:
            pytest.fail(f"Failed to parse timestamp: {timestamp_text}")

def test_message_sending(driver):
    driver.get("http://localhost:5000")
    
    # Wait for and find the message input
    message_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "message-input"))
    )
    
    # Type and send a test message
    test_message = "Test message from Selenium"
    message_input.send_keys(test_message)
    
    # Find and click send button
    send_button = driver.find_element(By.ID, "send-button")
    send_button.click()
    
    # Wait for the message to appear
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.xpath, f"//div[contains(text(), '{test_message}')]"))
    )

def test_add_sleep_record_validation(driver):
    driver.get("http://localhost:5000/add")
    
    # Test case where wake time is before sleep time
    sleep_time = datetime.now()
    wake_time = sleep_time - timedelta(hours=1)
    
    sleep_input = driver.find_element(By.ID, "sleep_time")
    wake_input = driver.find_element(By.ID, "wake_time")
    
    sleep_input.send_keys(sleep_time.strftime("%Y-%m-%dT%H:%M"))
    wake_input.send_keys(wake_time.strftime("%Y-%m-%dT%H:%M"))
    
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    # Check if error message is displayed
    error_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
    )
    assert "Czas pobudki musi być późniejszy niż czas zaśnięcia" in error_message.text

def test_sleep_duration_calculation(driver):
    driver.get("http://localhost:5000/add")
    
    # Add a sleep record with known duration
    sleep_time = datetime.now() - timedelta(hours=2)
    wake_time = datetime.now() - timedelta(hours=1)
    
    sleep_input = driver.find_element(By.ID, "sleep_time")
    wake_input = driver.find_element(By.ID, "wake_time")
    
    sleep_input.send_keys(sleep_time.strftime("%Y-%m-%dT%H:%M"))
    wake_input.send_keys(wake_time.strftime("%Y-%m-%dT%H:%M"))
    
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    # Verify duration on the main page
    driver.get("http://localhost:5000")
    duration_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "duration"))
    )
    assert "1h 0min" in duration_element.text

def test_nap_timer(driver):
    driver.get("http://localhost:5000")
    
    # Start nap timer
    start_button = driver.find_element(By.ID, "napButton")
    start_button.click()
    
    # Wait for timer to appear and verify initial values
    timer_container = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "timer-container"))
    )
    hours = driver.find_element(By.ID, "hours").text
    minutes = driver.find_element(By.ID, "minutes").text
    seconds = driver.find_element(By.ID, "seconds").text
    
    assert hours == "00"
    assert minutes == "00"
    assert seconds == "00"
    
    # Wait for 5 seconds and verify timer updates
    time.sleep(5)
    
    seconds = driver.find_element(By.ID, "seconds").text
    assert int(seconds) >= 5

def test_timezone_handling(driver):
    driver.get("http://localhost:5000/add")
    
    # Add a sleep record
    local_tz = pytz.timezone('Europe/Warsaw')
    current_time = datetime.now(local_tz)
    sleep_time = current_time - timedelta(hours=1)
    wake_time = current_time
    
    sleep_input = driver.find_element(By.ID, "sleep_time")
    wake_input = driver.find_element(By.ID, "wake_time")
    
    sleep_input.send_keys(sleep_time.strftime("%Y-%m-%dT%H:%M"))
    wake_input.send_keys(wake_time.strftime("%Y-%m-%dT%H:%M"))
    
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    # Verify the time is displayed in local timezone
    driver.get("http://localhost:5000")
    record_time = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".record-card p"))
    )
    
    displayed_time = record_time.text.split(" - ")
    assert len(displayed_time) == 2
    
    # Verify the times are in HH:MM format
    for time_str in displayed_time:
        try:
            datetime.strptime(time_str.strip(), "%H:%M")
        except ValueError:
            pytest.fail(f"Invalid time format: {time_str}")

def test_edit_sleep_record(driver):
    driver.get("http://localhost:5000")
    
    # Click edit on the first record
    edit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".record-actions .button.small"))
    )
    edit_button.click()
    
    # Try to set invalid times (wake time before sleep time)
    sleep_time = datetime.now()
    wake_time = sleep_time - timedelta(minutes=30)
    
    sleep_input = driver.find_element(By.ID, "sleep_time")
    wake_input = driver.find_element(By.ID, "wake_time")
    
    sleep_input.clear()
    wake_input.clear()
    
    sleep_input.send_keys(sleep_time.strftime("%Y-%m-%dT%H:%M"))
    wake_input.send_keys(wake_time.strftime("%Y-%m-%dT%H:%M"))
    
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    # Check if error message is displayed
    error_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
    )
    assert "Czas pobudki musi być późniejszy niż czas zaśnięcia" in error_message.text 