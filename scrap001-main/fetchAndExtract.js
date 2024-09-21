async function fetchAndExtract(url) {
    try {
        const response = await fetch(url);
        const htmlContent = await response.text();
        console.log(htmlContent);
    } catch (error) {
        console.error("Failed to download HTML from the specified URL:", error);
    }
}

const url = process.argv[2];
if (url) {
    fetchAndExtract(url);
} else {
    console.error("No URL provided.");
}