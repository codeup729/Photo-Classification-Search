// Initialize the API Gateway client with static IAM credentials
const apigClient = apigClientFactory.newClient({
    accessKey: '<AWS_ACCESS_KEY>', // Replace with your AWS Access Key
    secretKey: '<AWS_SECRET_KEY>', // Replace with your AWS Secret Key
    region: 'us-east-1',           // Replace with your AWS region
    defaultContentType: 'application/json',
    defaultAcceptType: 'application/json'
});

// Search Photos
async function searchPhotos(query) {
    try {
        const params = { q: query }; // Query parameter for the API
        const additionalParams = {}; // No need for API key

        // Call the API Gateway's GET /search endpoint
        const response = await apigClient.searchGet(params, null, additionalParams);
        displayResults(response.data.results); // Display search results
    } catch (error) {
        console.error("Error fetching search results:", error);
        alert("Failed to fetch search results. Please try again.");
    }
}

// Display Search Results
function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear previous results

    if (results.length === 0) {
        resultsContainer.innerHTML = '<p>No photos found for your query.</p>';
        return;
    }

    // Loop through the results and create HTML elements for each photo
    results.forEach(photo => {
        const photoElement = document.createElement('div');
        photoElement.className = 'photo';
        photoElement.innerHTML = `
            <img src="https://${photo.bucket}.s3.amazonaws.com/${photo.objectKey}" alt="${photo.objectKey}" />
            <p><strong>Labels:</strong> ${photo.labels.join(', ')}</p>
        `;
        resultsContainer.appendChild(photoElement);
    });
}

// Upload Photo
async function uploadPhoto(file, customLabels = []) {
    try {
        const additionalParams = {
            headers: {
                'Content-Type': file.type,
                ...(customLabels.length > 0 && { 'X-Amz-Meta-CustomLabels': customLabels.join(', ') }) // Add header only if customLabels exist
            }
        };

        const params = { object: file.name }; // S3 object key
        const body = file; // File object to upload

        // Call the API Gateway's PUT /upload endpoint
        const response = await apigClient.uploadPut(params, body, additionalParams);
        alert("Photo uploaded successfully!");
    } catch (error) {
        console.error("Error uploading photo:", error);
        alert("Failed to upload photo. Please try again.");
    }
}

// Handle Search Button Click
document.getElementById('searchButton').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        searchPhotos(query); // Call searchPhotos function
    } else {
        alert("Please enter a search term.");
    }
});

// Handle Upload Form Submission
document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = document.getElementById('fileInput').files[0];
    const customLabelsInput = document.getElementById('customLabels').value.trim();
    const customLabels = customLabelsInput ? customLabelsInput.split(',').map(label => label.trim()) : []; // Parse custom labels or use an empty array

    if (file) {
        await uploadPhoto(file, customLabels); // Call uploadPhoto function
    } else {
        alert("Please select a file.");
    }
});
