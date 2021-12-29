"""
Retrieves metadata about companies from LinkedIn and adds it to README.md.

Requires LinkedIn account details to query API. Enter at beginning of the script or 
save in .env file (as LINKEDIN_EMAIL and LINKEDIN_PASSWORD).
"""

import re
import os
import getpass
from linkedin_api import Linkedin
from dotenv import load_dotenv
import typer
from rich.traceback import install


install(show_locals=True)


def main(skip_existing: bool = False, force: bool = False):
    """
    Pull company metadata from LinkedIn and write to tags in README.md.

    Add tags <!--linkedin:company_name--><!--endlinkedin--> to README.md, where
    `company_name` corresponds to the last piece of the company's LinkedIn URL.
    """

    # Read LinkedIn account details from .env or terminal.
    load_dotenv()
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    if email is None or password is None:
        typer.echo("Enter LinkedIn account to query the API (or use .env file)")
        typer.echo(
            "WARNING: Accounts with excessive API calls are sometimes blocked "
            "by LinkedIn."
        )
        email = input("LinkedIn email: ")
        password = getpass.getpass()
    else:
        typer.echo("LinkedIn account details read from .env")

    # Set up LinkedIn API.
    api = Linkedin(email, password, refresh_cookies=True)

    def create_company_description(name):
        """Create a markup description of the company from its LinkedIn `name`."""
        company = api.get_company(name)

        # Number of staff members.
        staff = company["staffCount"]
        staff_url = f"https://www.linkedin.com/company/{name}/people/"
        md = f" &nbsp;[👷 {staff}]({staff_url})"

        # Number of job openings.
        # Search for all jobs by the (full) company name first.
        # For generic company names, this will return a lot of false positives.
        full_name = company["name"]
        jobs_list = api.search_jobs(full_name, location_name="Berlin, Germany")
        # Then, filter by the company URN (unique identifier from LinkedIn).
        urn = company["entityUrn"]
        filtered_jobs_list = [
            job for job in jobs_list if job["companyDetails"].get("company", "") == urn
        ]
        jobs = len(filtered_jobs_list)
        if jobs > 0:
            jobs_url = f"https://www.linkedin.com/company/{name}/jobs/"
            md += f" &nbsp;[🔎 {jobs}]({jobs_url})"

        # Funding round.
        if "fundingData" in company:
            funding_type = company["fundingData"]["lastFundingRound"]["fundingType"]
            # Only show "Seed" or "Series X", otherwise show "X rounds" (there are some
            # other weird funding type names).
            if funding_type in ["SEED", "SERIES_A", "SERIES_B", "SERIES_C", "SERIES_D"]:
                funding = funding_type.replace("_", " ").title()
            else:
                funding_rounds = company["fundingData"]["numFundingRounds"]
                funding = f"{funding_rounds} round"
                if funding_rounds > 1:
                    funding += "s"
            funding_url = company["fundingData"]["fundingRoundListCrunchbaseUrl"]
            md += f" &nbsp;[💰 {funding}]({funding_url})"

        return md

    # Read README.md.
    with open("README.md", "r") as f:
        text = f.read()

    # Replace old descriptions with new ones.
    typer.echo("-" * 80)
    for name, old_desc in re.findall(
        "<!--linkedin:(.*?)-->(.*?)<!--endlinkedin-->", text
    ):
        if skip_existing and old_desc:
            typer.echo(name + ": skipped")
        else:
            typer.echo(name + ":")
            new_desc = create_company_description(name)
            typer.echo(new_desc)
            text = text.replace(
                f"<!--linkedin:{name}-->{old_desc}<!--endlinkedin-->",
                f"<!--linkedin:{name}-->{new_desc}<!--endlinkedin-->",
            )
            typer.echo()

    # typer.echo updated file content.
    typer.echo("-" * 80)
    typer.echo()
    typer.echo(text)
    typer.echo()
    typer.echo("-" * 80)

    # Write to file.
    if force:
        write = "y"
    else:
        write = input("Review modified text above. Write to README.md? (Y/n) ")
    if write.lower() in ["", "y", "yes"]:
        os.rename("README.md", "old-README.md")
        with open("README.md", "w") as f:
            f.write(text)
        typer.secho("✓ Updated README.md (old file stored in old-README.md", fg="green")
    else:
        typer.secho("✗ Did NOT update README.md", fg="red")


if __name__ == "__main__":
    typer.run(main)
