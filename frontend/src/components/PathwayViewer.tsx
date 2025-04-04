import React from "react";

interface PathwayViewerProps {
  url: string;
  companyName: string;
}

const PathwayViewer: React.FC<PathwayViewerProps> = ({ url, companyName }) => {
  return (
    <div className="border border-gray-300 rounded shadow-lg bg-white">
      <h2 className="text-xl font-semibold p-4 bg-gray-50 border-b border-gray-200">
        Energy Transition Pathway for {companyName}
      </h2>
      <iframe
        src={url}
        title={`Energy Transition Pathway for ${companyName}`}
        style={{ width: "100%", height: "80vh", border: "none" }}
        // Consider adding sandbox attributes for security if content isn't fully trusted
        // sandbox="allow-scripts allow-same-origin"
      />
    </div>
  );
};

export default PathwayViewer;
