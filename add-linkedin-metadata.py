"""
Retrieves metadata about companies from LinkedIn and adds it to README.md.

Set tags <!--linkedin:company_name--><!--endlinkedin--> in README.md to specify 
where to add metadata. `company_name` should correspond to the unique company name on
LinkedIn (it's the last piece of the URL of the company's LinkedIn page).

The script asks for LinkedIn email/password at startup to access the API. Old readme 
file is backed up to `old-README.md` (make sure to keep that in .gitignore!)
"""

import re
import os
import getpass
from linkedin_api import Linkedin


# Set up LinkedIn API.
email = input("LinkedIn email: ")
password = getpass.getpass()
api = Linkedin(email, password)


def create_company_description(name):
    """Create a markup description of the company from its LinkedIn `name`."""
    company = api.get_company(name)

    # Staff members.
    staff = company["staffCount"]
    staff_url = f"https://www.linkedin.com/company/{name}/people/"
    md = f" &nbsp;[👷{staff}]({staff_url})"

    # Funding round.
    if "fundingData" in company:
        funding = (
            company["fundingData"]["lastFundingRound"]["fundingType"]
            .replace("_", " ")
            .title()
        )
        funding_url = company["fundingData"]["fundingRoundListCrunchbaseUrl"]
        md += f" &nbsp;[💰 {funding}]({funding_url})"

    # Job openings.
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
    jobs_url = f"https://www.linkedin.com/company/{name}/jobs/"
    md += f" &nbsp;[🎯 {jobs}]({jobs_url})"

    return md


# Read README.md.
with open("README.md", "r") as f:
    text = f.read()

# Replace old descriptions with new ones.
print("-" * 80)
for name, old_desc in re.findall("<!--linkedin:(.*?)-->(.*?)<!--endlinkedin-->", text):
    print(name + ":")
    new_desc = create_company_description(name)
    print(new_desc)
    text = text.replace(
        f"<!--linkedin:{name}-->{old_desc}<!--endlinkedin-->",
        f"<!--linkedin:{name}-->{new_desc}<!--endlinkedin-->",
    )
    print()

# Print updated file content.
print("-" * 80)
print()
print(text)
print()
print("-" * 80)

# Write to file.
write = input("Write modified text above to README.md? (Y/n) ")
if write.lower() in ["", "y", "yes"]:
    os.rename("README.md", "old-README.md")
    with open("README.md", "w") as f:
        f.write(text)
    print("✓ Updated README.md (old file stored in old-README.md")
else:
    print("✗ Did NOT update README.md")
