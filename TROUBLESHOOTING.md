# Troubleshooting Guide

## Face Registration Issues

### Error: "You cannot access body after reading from request's data stream"

**Problem**: This error occurs when the Django request body is read multiple times.

**Solution**: ✅ **FIXED** - Updated API views to use `request.data` instead of `json.loads(request.body)`

**What was changed**:
- `api_validate_image` view now uses `request.data.get('image_data')`
- `api_recognize_face` view now uses `request.data.get('image_data')`
- Removed `@csrf_exempt` decorator as it's not needed with DRF `@api_view`

### Face Recognition Service Not Available

**Problem**: "Face recognition service not available" message

**Solutions**:
1. **Install DeepFace**:
   ```bash
   pip install deepface opencv-python tensorflow
   ```

2. **Check Installation**:
   ```python
   python -c "from deepface import DeepFace; print('DeepFace installed successfully')"
   ```

3. **Alternative**: The system will work without DeepFace for basic functionality, but face recognition will be disabled.

### Camera Access Issues

**Problem**: Camera not starting or permission denied

**Solutions**:
1. **Browser Permissions**: Ensure camera permissions are granted
2. **HTTPS Required**: For production, camera access requires HTTPS
3. **Browser Compatibility**: Test with Chrome/Firefox/Edge
4. **Device Issues**: Check if camera is being used by another application

### Image Validation Failures

**Problem**: "Image validation failed" messages

**Solutions**:
1. **Lighting**: Ensure good lighting conditions
2. **Face Position**: Center face in camera view
3. **Image Quality**: Use high-resolution camera if possible
4. **Single Face**: Ensure only one face is visible

## Testing the Fix

Run the test script to verify the API endpoints:

```bash
python test_face_enrollment.py
```

Expected output:
```
✅ All tests passed! The face enrollment should work correctly.
```

## Step-by-Step Testing

1. **Start Django Server**:
   ```bash
   python manage.py runserver
   ```

2. **Create Test Student**:
   - Go to `http://localhost:8000/signup/`
   - Fill in student details
   - Create account

3. **Test Face Registration**:
   - Should automatically redirect to face registration
   - Click "Start Camera"
   - Position face and click "Capture Face"
   - Should show "Image captured successfully!"
   - Click "Complete Registration"

4. **Verify Success**:
   - Should redirect to student dashboard
   - Face registration status should show as completed

## Common Issues and Solutions

### Issue: "DeepFace not available"
**Solution**: Install required packages or continue without face recognition

### Issue: Camera not working
**Solution**: Check browser permissions and try different browser

### Issue: Face not recognized during attendance
**Solution**: 
- Re-register face with better lighting
- Ensure face is clearly visible
- Check if student is enrolled in the class

### Issue: API endpoints returning 500 errors
**Solution**: 
- Check Django server logs
- Verify database migrations are applied
- Ensure all required packages are installed

## Development Tips

1. **Debug Mode**: Keep `DEBUG = True` during development
2. **Logging**: Check Django logs for detailed error messages
3. **Browser Console**: Check browser console for JavaScript errors
4. **Network Tab**: Monitor network requests in browser dev tools

## Production Considerations

1. **HTTPS**: Required for camera access in production
2. **Database**: Use PostgreSQL/MySQL instead of SQLite
3. **Media Files**: Configure proper media file serving
4. **Security**: Update security settings for production
5. **Performance**: Consider face recognition optimization for large datasets

## Getting Help

If issues persist:
1. Check Django server logs for detailed error messages
2. Verify all dependencies are installed correctly
3. Test with different browsers and devices
4. Review the README.md for setup instructions
