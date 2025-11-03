# Stage 5 Frontend Validation Guide

## Prerequisites

1. **Backend API Running**: The backend must be running at `http://localhost:8000`
   ```bash
   cd /Users/prabhugovindan/working/hackathon
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend Dependencies Installed**:
   ```bash
   cd frontend
   npm install
   ```

## Starting the Frontend

```bash
cd frontend
npm run dev
```

The frontend will start at: **http://localhost:3000**

## Chrome Browser Validation

### Step 1: Open Chrome and Navigate

1. Open **Google Chrome** browser
2. Navigate to: `http://localhost:3000`
3. You should see the **TBAML System** header

### Step 2: Test the UC1 Input Form

**Test Case 1: Form Validation**
- Leave fields empty and click "Verify Line of Business"
- ✅ Should show validation errors for required fields

**Test Case 2: Invalid Country Code**
- Enter country code "USA" (3 characters)
- ✅ Should show error: "Country code must be 2 characters"

**Test Case 3: Valid Form Submission**
- Client: `Shell plc`
- Country: `GB` (2 letters)
- Role: `Export` (from dropdown)
- Product: `Oil & Gas`
- Click "Verify Line of Business"
- ✅ Should show loading spinner
- ✅ Should display results after completion

### Step 3: Verify Results Display

After form submission, verify:

1. **Verification Results Section**
   - ✅ Shows Verification ID
   - ✅ Shows Client name
   - ✅ Shows Country code
   - ✅ Shows Role

2. **Activity Level Indicator**
   - ✅ Shows activity level (Active/Dormant/Inactive/Suspended/Unknown)
   - ✅ Color-coded indicator is visible
   - ✅ Icon displayed correctly

3. **Flags & Alerts Display**
   - ✅ Flags are listed
   - ✅ Color coding based on severity:
     - Red for [HIGH]
     - Yellow for [MEDIUM]
     - Blue for [LOW]
   - ✅ Red Flag badge if `is_red_flag: true`

4. **Source Citation**
   - ✅ Data sources listed
   - ✅ Website source link (if available)
   - ✅ Sources formatted correctly

5. **AI Response**
   - ✅ AI analysis text displayed
   - ✅ "Show More/Show Less" button works
   - ✅ Text is readable and formatted

6. **Timeline**
   - ✅ Data collected timestamp
   - ✅ Publication date (if available)
   - ✅ Last verified timestamp
   - ✅ Created timestamp
   - ✅ Data freshness score
   - ✅ Confidence score

### Step 4: Test Error Handling

**Test Case: Backend Not Running**
1. Stop the backend API
2. Submit the form
3. ✅ Should display error message
4. ✅ Error message is clear and user-friendly

**Test Case: Invalid API Response**
1. Start backend with errors
2. Submit form
3. ✅ Should handle errors gracefully
4. ✅ Error UI is visible

### Step 5: Test Responsive Design

**Test in Chrome DevTools:**
1. Open Chrome DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M / Cmd+Shift+M)
3. Test at different viewports:
   - Mobile (375px)
   - Tablet (768px)
   - Desktop (1920px)
4. ✅ Layout adapts correctly
5. ✅ Components are readable
6. ✅ Forms are usable on mobile

### Step 6: Test Loading States

**During API Call:**
1. Submit form
2. ✅ Loading spinner appears
3. ✅ Form is disabled during submission
4. ✅ Button shows "Verifying..." text

### Step 7: Test Network Requests

**In Chrome DevTools Network Tab:**
1. Open Network tab
2. Submit form
3. ✅ API request to `/api/v1/lob/verify` is visible
4. ✅ Request payload is correct
5. ✅ Response status is 200
6. ✅ Response contains UC1 outputs

## Validation Checklist

- [ ] Frontend loads without errors
- [ ] Form validation works
- [ ] Form submission works
- [ ] Loading states display correctly
- [ ] Results display all components
- [ ] Activity indicator shows correctly
- [ ] Flags display with color coding
- [ ] Source citation is visible
- [ ] AI response is displayed
- [ ] Timeline shows timestamps
- [ ] Error handling works
- [ ] Responsive design works
- [ ] Network requests are correct
- [ ] All components render properly

## Common Issues

### CORS Errors
- **Solution**: Check that backend CORS is configured for `http://localhost:3000`

### API Connection Refused
- **Solution**: Make sure backend is running at `http://localhost:8000`

### Tailwind CSS Not Working
- **Solution**: Check that `postcss.config.js` and `tailwind.config.js` exist

### TypeScript Errors
- **Solution**: Run `npm run build` to check for TypeScript errors

## Expected Behavior

✅ **All components should:**
- Display correctly with proper styling
- Handle loading states gracefully
- Show error messages when needed
- Be responsive across screen sizes
- Follow accessibility best practices

## Success Criteria

**Stage 5 is validated if:**
1. ✅ Frontend starts without errors
2. ✅ Form accepts UC1 inputs
3. ✅ Results display all UC1 outputs
4. ✅ All components render correctly
5. ✅ Responsive design works
6. ✅ Error handling works
7. ✅ Loading states work
8. ✅ Chrome DevTools shows no console errors

