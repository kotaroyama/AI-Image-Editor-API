import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { triggerAutomaticDownload } from "../services/download.ts"
import { formatTimestamp } from "../services/date.ts"

type Job = {
  id: string,
  image_id: string,
  original_filename: string,
  action: string,
  status: string,
  created_at: string,
  url: string,
  error_message: string,
};

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);

  async function loadJobs() {
    const response = await api.get<Job[]>("/me/jobs");
    const data = response.data;

    let completedJobs: Job[] = [];

    data.forEach(job => {
      if (job.status === "COMPLETED") {
        completedJobs.push(job);
      }
    })

    setJobs(completedJobs);
  }

  useEffect(() => {
    loadJobs();
  }, []);

  return (
    <div>
      <h3>Last 10 Jobs</h3>
      {jobs.toSorted((a, b) => b.created_at.localeCompare(a.created_at)).map((job: Job) => (
        <div key={job.id}>
          <img
            src={ job.url }
            alt={ job.original_filename }
            width="600"
          />
          <p>{ job.action }</p>
          <Link
            to={`/photos/${job.image_id}`}
          >
            { job.original_filename }
          </Link>
          <span > | </span>
          <button
            onClick={() =>
              triggerAutomaticDownload(
                job.url,
                job.action,
                job.original_filename,
              )
            }
          >
            Download
          </button>
          <p>Job requested at { formatTimestamp(job.created_at) }</p>
        </div>
      ))}
    </div>
  )
}