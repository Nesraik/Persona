import React from 'react';

interface VideoCardProps {
  url: string;
}

// Helper function to extract the YouTube video ID from various URL formats
function getYouTubeID(url: string): string | null {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);

  if (match && match[2].length === 11) {
    return match[2];
  } else {
    return null;
  }
}

const VideoCard: React.FC<VideoCardProps> = ({ url }) => {
  const videoId = getYouTubeID(url);

  if (!videoId) {
    return <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>;
  }

  const embedUrl = `https://www.youtube.com/embed/${videoId}`;

  return (
    <div className="video-card" style={{
      position: 'relative',
      paddingBottom: '56.25%',
      height: 0,
      overflow: 'hidden',
      maxWidth: '100%',
      background: '#000',
      borderRadius: '8px', 
      margin: '10px 0' 
    }}>
      <iframe
        src={embedUrl}
        title="YouTube video player"
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
};

export default VideoCard;