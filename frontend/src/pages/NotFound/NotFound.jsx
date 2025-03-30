import React from 'react';
import Button from "../../components/Button/Button"

const NotFound = () => {
    return (
        <div class="notfound text-dark">
            <div class="d-flex align-items-center justify-content-center min-vh-100 px-2">
                <div class="text-center">
                    <h1 class="display-1 fw-bold">404</h1>
                    <p class="fs-2 fw-medium mt-4">Oops! Page not found</p>
                    <p class="mt-4 mb-5">The page you're looking for doesn't exist or has been moved.</p>
                    <Button> Go Home</Button>
                </div>
            </div>
        </div>
    )
}
export default NotFound;