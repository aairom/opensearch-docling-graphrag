# Background Job Queue Integration Guide

## Overview

The background job queue system allows users to submit document processing jobs and navigate away while processing continues in the background. This document explains how to integrate it with the Streamlit UI.

## Architecture

```
User Upload → Submit Job → Job Queue (SQLite) → Background Workers → Process Document
                ↓                                        ↓
           Job ID returned                      Update progress/status
                ↓                                        ↓
        Navigate away freely                    Store results
                ↓                                        ↓
        Check Jobs tab                          Complete/Failed
```

## Components

### 1. JobManager (`src/job_queue/job_manager.py`)
- SQLite-based job persistence
- Multi-threaded background workers
- Job status tracking
- Progress updates
- Thread-safe operations

### 2. Document Handler (`src/job_queue/document_handler.py`)
- `process_document_job()` - Single document processing
- `process_batch_job()` - Batch processing
- Progress updates at each step
- Error handling

### 3. Job Statuses
- `PENDING` - Waiting in queue
- `PROCESSING` - Currently being processed
- `COMPLETED` - Successfully finished
- `FAILED` - Error occurred
- `CANCELLED` - Manually cancelled

## Integration Steps

### Step 1: Update app.py Imports

```python
# Add to imports
from src.job_queue import JobManager, JobStatus
from src.job_queue.document_handler import process_document_job, process_batch_job
import atexit
```

### Step 2: Initialize Job Manager in Session State

```python
# Add to session state initialization
if 'job_manager' not in st.session_state:
    st.session_state.job_manager = None

def initialize_clients():
    """Initialize all clients including job manager."""
    try:
        with st.spinner("Initializing clients..."):
            if not st.session_state.initialized:
                # ... existing client initialization ...
                
                # Initialize job manager
                st.session_state.job_manager = JobManager(
                    db_path="jobs.db",
                    max_workers=2  # Adjust based on resources
                )
                
                # Register handlers
                st.session_state.job_manager.register_handler(
                    'process_document',
                    process_document_job
                )
                st.session_state.job_manager.register_handler(
                    'process_batch',
                    process_batch_job
                )
                
                # Start workers
                st.session_state.job_manager.start()
                
                st.session_state.initialized = True
                st.success("✅ All clients initialized successfully!")
                
    except Exception as e:
        st.error(f"❌ Error initializing clients: {str(e)}")
        logger.error(f"Initialization error: {str(e)}")

# Cleanup on exit
def cleanup():
    if st.session_state.get('job_manager'):
        st.session_state.job_manager.stop()

atexit.register(cleanup)
```

### Step 3: Update Upload Document Tab

Replace synchronous processing with job submission:

```python
def upload_document_tab():
    st.header("📤 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'docx', 'pptx', 'html', 'md', 'txt', 'png', 'jpg', 'jpeg']
    )
    
    if uploaded_file:
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        if st.button("🚀 Process Document", type="primary"):
            try:
                # Save uploaded file temporarily
                temp_path = Path("input") / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Submit job instead of processing directly
                job_id = st.session_state.job_manager.submit_job(
                    job_type='process_document',
                    payload={
                        'file_path': str(temp_path),
                        'file_name': uploaded_file.name,
                        'document_id': str(uuid.uuid4())
                    },
                    priority=1  # High priority for user uploads
                )
                
                st.success(f"✅ Job submitted successfully!")
                st.info(f"📋 Job ID: `{job_id}`")
                st.info("🔄 Processing in background. Check the **Jobs** tab for status.")
                
                # Show link to jobs tab
                st.markdown("---")
                st.markdown("### Next Steps")
                st.markdown("1. Navigate to the **Jobs** tab to monitor progress")
                st.markdown("2. You can continue using the app while processing")
                st.markdown("3. Results will be saved to the `output` folder")
                
            except Exception as e:
                st.error(f"❌ Error submitting job: {str(e)}")
                logger.error(f"Job submission error: {str(e)}")
```

### Step 4: Update Batch Process Tab

```python
def batch_process_tab():
    st.header("📦 Batch Process Documents")
    
    input_dir = Path(settings.input_dir)
    
    # List files
    files = []
    for ext in ['*.pdf', '*.docx', '*.pptx', '*.html', '*.md', '*.txt']:
        files.extend(input_dir.glob(ext))
    
    if files:
        st.info(f"📁 Found {len(files)} documents in `{input_dir}`")
        
        # Show files
        with st.expander("📄 Files to process"):
            for f in files:
                st.text(f"• {f.name}")
        
        if st.button("🚀 Process All Documents", type="primary"):
            try:
                # Submit batch job
                job_id = st.session_state.job_manager.submit_job(
                    job_type='process_batch',
                    payload={
                        'input_dir': str(input_dir)
                    },
                    priority=0  # Normal priority for batch
                )
                
                st.success(f"✅ Batch job submitted!")
                st.info(f"📋 Job ID: `{job_id}`")
                st.info(f"📊 Processing {len(files)} documents in background")
                st.info("🔄 Check the **Jobs** tab for progress")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.warning(f"⚠️ No documents found in `{input_dir}`")
```

### Step 5: Add Jobs Status Tab

Add a new tab to the menu:

```python
# In main menu
selected = option_menu(
    menu_title=None,
    options=["Home", "Upload", "Batch Process", "Jobs", "Search", "Graph Explorer", "Settings"],
    icons=["house", "upload", "folder", "list-task", "search", "diagram-3", "gear"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal"
)

# Add Jobs tab handler
elif selected == "Jobs":
    jobs_status_tab()
```

### Step 6: Implement Jobs Status Tab

```python
def jobs_status_tab():
    st.header("📋 Job Queue Status")
    
    # Get statistics
    stats = st.session_state.job_manager.get_stats()
    
    # Display stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("Pending", stats['pending'], delta=None, delta_color="off")
    with col3:
        st.metric("Processing", stats['processing'], delta=None, delta_color="normal")
    with col4:
        st.metric("Completed", stats['completed'], delta=None, delta_color="normal")
    with col5:
        st.metric("Failed", stats['failed'], delta=None, delta_color="inverse")
    
    st.markdown("---")
    
    # Filter options
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Pending", "Processing", "Completed", "Failed"],
        index=0
    )
    
    # Get jobs
    if status_filter == "All":
        jobs = st.session_state.job_manager.get_all_jobs(limit=50)
    else:
        status_enum = JobStatus[status_filter.upper()]
        jobs = st.session_state.job_manager.get_all_jobs(status=status_enum, limit=50)
    
    # Display jobs
    if jobs:
        for job in jobs:
            with st.expander(
                f"{'🟢' if job['status'] == 'completed' else '🔴' if job['status'] == 'failed' else '🟡'} "
                f"{job['job_type']} - {job['job_id'][:8]}... ({job['status']})"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text(f"Job ID: {job['job_id']}")
                    st.text(f"Type: {job['job_type']}")
                    st.text(f"Status: {job['status']}")
                    st.text(f"Priority: {job['priority']}")
                
                with col2:
                    st.text(f"Created: {job['created_at']}")
                    if job['started_at']:
                        st.text(f"Started: {job['started_at']}")
                    if job['completed_at']:
                        st.text(f"Completed: {job['completed_at']}")
                
                # Progress bar
                if job['status'] == 'processing':
                    progress = job['progress'] or 0
                    st.progress(progress / 100, text=f"Progress: {progress}%")
                
                # Show payload
                if job['payload']:
                    with st.expander("📦 Payload"):
                        st.json(json.loads(job['payload']))
                
                # Show result
                if job['result']:
                    with st.expander("✅ Result"):
                        st.json(json.loads(job['result']))
                
                # Show error
                if job['error']:
                    st.error(f"Error: {job['error']}")
                
                # Actions
                if job['status'] in ['pending', 'processing']:
                    if st.button(f"Cancel Job", key=f"cancel_{job['job_id']}"):
                        st.session_state.job_manager.update_job_status(
                            job['job_id'],
                            JobStatus.CANCELLED
                        )
                        st.rerun()
    else:
        st.info("No jobs found")
    
    # Auto-refresh
    if st.checkbox("Auto-refresh (every 5 seconds)", value=False):
        time.sleep(5)
        st.rerun()
```

## Testing

### Test Single Document Processing

```python
# 1. Upload a document
# 2. Click "Process Document"
# 3. Navigate to Jobs tab
# 4. See job status updating
# 5. Navigate to other tabs (processing continues)
# 6. Return to Jobs tab to see completion
```

### Test Batch Processing

```python
# 1. Put files in ./input folder
# 2. Go to Batch Process tab
# 3. Click "Process All Documents"
# 4. Navigate away
# 5. Check Jobs tab for progress
```

## Configuration

### Adjust Worker Count

```python
# In initialize_clients()
st.session_state.job_manager = JobManager(
    db_path="jobs.db",
    max_workers=4  # Increase for more concurrent processing
)
```

### Job Priority

```python
# High priority (processed first)
job_id = job_manager.submit_job(
    job_type='process_document',
    payload={...},
    priority=10  # Higher number = higher priority
)

# Normal priority
job_id = job_manager.submit_job(
    job_type='process_document',
    payload={...},
    priority=0  # Default
)
```

## Database Management

### View Jobs Database

```bash
sqlite3 jobs.db "SELECT job_id, job_type, status, progress FROM jobs ORDER BY created_at DESC LIMIT 10;"
```

### Clean Old Jobs

```python
# Add to app.py
def cleanup_old_jobs():
    """Remove completed jobs older than 7 days."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM jobs 
        WHERE status IN ('completed', 'failed', 'cancelled')
        AND datetime(completed_at) < datetime('now', '-7 days')
    """)
    
    conn.commit()
    conn.close()
```

## Troubleshooting

### Jobs Not Processing

1. Check if workers are running:
```python
if st.session_state.job_manager.running:
    st.success("Workers are running")
else:
    st.error("Workers are not running")
    st.session_state.job_manager.start()
```

2. Check logs:
```bash
tail -f logs/app_*.log | grep "Job"
```

### Database Locked

If you see "database is locked" errors:
- Reduce max_workers
- Add retry logic
- Use WAL mode:

```python
conn = sqlite3.connect("jobs.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.close()
```

## Benefits

✅ **Navigate freely** - Submit job and move to other tabs
✅ **Concurrent processing** - Multiple documents at once
✅ **Progress tracking** - Real-time status updates
✅ **Error handling** - Failed jobs don't block others
✅ **Job history** - View past processing jobs
✅ **Priority queue** - Important jobs processed first
✅ **Persistent** - Jobs survive app restarts

## Made with Bob