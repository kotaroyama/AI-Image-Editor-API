import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { api } from "../services/api";
import { triggerAutomaticDownload } from "../services/download.ts"
import { formatTimestamp } from "../services/date.ts"
import { capitalize } from "../services/utils.ts";

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
      <Card className="relative mx-auto w-full max-w-sm pt-0">
        {jobs.toSorted((a, b) => b.created_at.localeCompare(a.created_at)).map((job: Job) => (
          <div key={job.id}>
            <img
              src={ job.url }
              alt={ job.original_filename }
              className="relative z-20 aspect-video w-full object-cover"
            />
            <CardHeader>
              <CardTitle>
                { capitalize(job.action) }
              </CardTitle>
            </CardHeader>
            <CardFooter>
              <Link
                to={`/photos/${job.image_id}`}
              >
                { job.original_filename }
              </Link>
              <Button
                onClick={async () =>
                  await triggerAutomaticDownload(job.url,)
                }
              >
                Download
              </Button>
            </CardFooter>
            <div className="text-sm">
              Job requested at { formatTimestamp(job.created_at) }
            </div>
          </div>
        ))}
      </Card>
    </div>
  )
}