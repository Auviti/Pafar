import React from 'react';

// A reusable Table component with customizable headers and data
const Table = ({ headers, data, className, ...props }) => {
  return (
    <div className={`table-responsive ${className}`} {...props}>
      <table className="table mb-0">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={index} className="border-gray-200" scope="col">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((transaction, index) => (
            <tr key={index}>
              {Object.values(transaction).map((value, idx) => (
                <td key={idx}>{value}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
