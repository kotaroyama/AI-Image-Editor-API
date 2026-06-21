import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
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
      <Helmet>
        <title>Jobs | AI Image Editor</title>
      </Helmet>
      
      <div className="mb-6 flex item-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Edited Photos
          </h2>
        </div>

        <p className="text-sm text-muted-foreground">
          {jobs.length} job{jobs.length !== 1 ? "s": ""}
        </p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        {jobs.toSorted((a, b) => b.created_at.localeCompare(a.created_at)).map((job: Job) => (
          <Card
            key={job.id}
            className="overflow-hidden"
          >
            <img
              src={ job.url }
              alt={ job.original_filename }
              className="aspect-square w-full object-cover"
            />

            <CardHeader>
              <CardTitle className="truncate">
                { capitalize(job.action) }
              </CardTitle>
            </CardHeader>

            <CardFooter className="gap-2">
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
            <div className="px-6 pb-4 text-xs text-muted-foreground">
              Requested {formatTimestamp(job.created_at)}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}