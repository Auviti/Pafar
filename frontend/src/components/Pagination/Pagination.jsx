import { useEffect, useState } from "react";
import PropTypes from 'prop-types';
import './Pagination.css';

const Pagination = ({ items = [], onSelect, onPrev, onNext, position = 'right', itemsPerPage = 12 }) => {
    const [currentPage, setCurrentPage] = useState(1); // Track the current page number
    // Calculate total pages based on the cards length and items per page
    const totalPages = Math.ceil(items.length / itemsPerPage);
    
    // Function to handle page selection
    const handlePageSelect = (pageNumber) => {
        setCurrentPage(pageNumber);
        if (onSelect) onSelect(pageNumber); // Call onSelect if passed as a prop
    };

    // Handle previous page click
    const handlePrevClick = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1);
            if (onPrev) onPrev(currentPage - 1);
        }
    };

    // Handle next page click
    const handleNextClick = () => {
        if (currentPage < totalPages) {
            setCurrentPage(currentPage + 1);
            if (onNext) onNext(currentPage + 1);
        }
    };

    // Generate page numbers for display (1 per page)
    const pageNumbers = [];
    for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
    }

    // Slice page numbers to display based on current page
    const displayPages = pageNumbers.slice(
        Math.max(0, currentPage - 3), // Ensure the display is within bounds
        Math.min(currentPage + 2, totalPages) // Ensure we don't go beyond total pages
    );

    const renderPagination = (
        <nav aria-label="pagination">
            <div className={`d-flex justify-content-between align-items-center`}>
                <ul className="pagination">
                    {/* Previous Button */}
                    <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                        <a className="page-link" href="javascript:void(0)" onClick={handlePrevClick} aria-disabled={currentPage === 1}>
                            <svg xmlns="http://www.w3.org/2000/svg" width={21} height={21} viewBox="0 0 21 21" style={{ transform: `rotate(-90deg)` }}>
                                <path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" d="m14.5 7.5l-4-4l-4.029 4m4.029-4v13" strokeWidth={1}></path>
                            </svg>
                        </a>
                    </li>

                    {/* Page Numbers */}
                    {displayPages.map((pageNumber) => (
                        <li key={pageNumber} className={`page-item ${pageNumber === currentPage ? 'active' : ''}`}>
                            <a className="page-link" href="javascript:void(0)" onClick={() => handlePageSelect(pageNumber)}>
                                {pageNumber}
                            </a>
                        </li>
                    ))}
                    {/* Next Button */}
                    <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                        <a className="page-link" href="javascript:void(0)" onClick={handleNextClick} aria-disabled={currentPage === totalPages}>
                            <svg xmlns="http://www.w3.org/2000/svg" width={21} height={21} viewBox="0 0 21 21" style={{ transform: `rotate(90deg)` }}>
                                <path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" d="m14.5 7.5l-4-4l-4.029 4m4.029-4v13" strokeWidth={1}></path>
                            </svg>
                        </a>
                    </li>
                </ul>
            </div>
        </nav>
    );

    return (
        <div className='d-flex justify-content-between align-items-center p-2'>
            {position === 'left' ? renderPagination : <span></span>}
            {position === 'center' ? renderPagination : <span></span>}
            {position === 'right' ? renderPagination : <span></span>}
        </div>
    );
};

// Define prop types
Pagination.propTypes = {
    items: PropTypes.array.isRequired, // Expected an array of items
    onSelect: PropTypes.func,  // Expected a function for selecting a page
    onPrev: PropTypes.func,    // Expected a function for previous page action
    onNext: PropTypes.func,    // Expected a function for next page action
    position: PropTypes.oneOf(['left', 'center', 'right']),  // Expected 'left', 'center', or 'right' for position
    itemsPerPage: PropTypes.number, // Expected a number for items per page (default 12)
};

// Default props
Pagination.default = {
    itemsPerPage: 12, // Default to 12 items per page
};

export default Pagination;
