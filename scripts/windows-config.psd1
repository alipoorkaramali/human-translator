@{
    # Open Excel after each processed file
    OpenExcel  = $false

    # Open output folder after process.bat
    OpenFolder = $true

    # Debounce before processing (ms) — wait until editor finishes Save
    DebounceMs = 900

    # Poll interval backup (ms)
    PollMs     = 1000

    # Write data/output/processor.log
    LogToFile  = $true

    # Smoke test after setup
    SmokeTest  = $true

    # When watch starts, process files already sitting in data/input
    ProcessExistingOnStart = $false
}
