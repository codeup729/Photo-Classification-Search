// Initialize the API Gateway client with static IAM credentials
const apigClient = apigClientFactory.newClient({
    accessKey: 'AKIAQZFG5JYFOWX7IPWN', // Replace with your AWS Access Key
    secretKey: 'cUYO45lmYXiV9CznJiVLvM5HvJaVv165xYs2Q5kq', // Replace with your AWS Secret Key
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

        // If the response contains image data, display it
        const result = JSON.parse(response.data.body);
        if (result.image) {
            displayResults(result);
        } else {
            alert(result.message || "No matching photos found.");
        }
    } catch (error) {
        console.error("Error fetching search results:", error);
        alert("Failed to fetch search results. Please try again.");
    }
}



// Display Search Results
function displayResults(result) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear previous results

    // Create a container for the photo
    const photoElement = document.createElement('div');
    photoElement.className = 'photo';

    // Set the image and metadata
    photoElement.innerHTML = `
        <img src="data:image/jpeg;base64,${result.image}" alt="${result.objectKey}" />
        <p><strong>Object Key:</strong> ${result.objectKey}</p>
        <p><strong>Bucket:</strong> ${result.bucket}</p>
        <p><strong>Labels:</strong> ${result.labels.join(', ')}</p>
    `;

    resultsContainer.appendChild(photoElement);
}


// Upload Photo
async function uploadPhoto(file, customLabels = [], bucketName = 'b2-buckett') {
    try {
        // Define parameters for the API call
        const params = {
            bucket: bucketName, // Replace with your bucket name
            filename: file.name // File name
        };

        // Define headers for the API call
        const headers = {
            'Content-Type': file.type, // File MIME type
            'X-Amz-Meta-CustomLabels': customLabels.length > 0 ? customLabels.join(', ') : '' // Custom labels as metadata
        };

        // Additional parameters for the API call
        const additionalParams = {
            headers: headers
        };

        // File data to be uploaded
        const body = file;

        // Debugging logs
        console.log('Params:', params);
        console.log('Headers:', headers);
        console.log('Additional Params:', additionalParams);

        // Make the API call using apigClient
        const response = await apigClient.uploadBucketFilenamePut(params, body, additionalParams);

        // Log response and notify the user
        console.log("Upload response:", response);
        alert("Photo uploaded successfully!");
    } catch (error) {
        // Error handling and logging
        console.error("Full Error Object:", error);
        console.error("Error uploading photo:", error.message);
        if (error.response) {
            console.error("Error Response:", error.response);
            alert(`Failed to upload photo: ${error.response.data?.message || error.message}`);
        } else {
            alert(`Failed to upload photo: ${error.message}`);
        }
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
