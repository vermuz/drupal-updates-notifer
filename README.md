# Drupal available updates collector
Leverages drush to query available drupal updates on multiple remotes and collate the results into a single Amazon SNS notification.

## Setup
As indicated by the boto documentation, users need to set the following environment variables:

```bash
export AWS_ACCESS_KEY_ID="<Insert your AWS Access Key>"
export AWS_SECRET_ACCESS_KEY="<Insert your AWS Secret Key>"
```

Copy siteOptions.py.example to siteOptions.py and populate values.

## Use/Switches
- -c : Clear updates cache before checking for update (optional)
- -t : Destination SNS topic ARN

## Dependencies :
+   boto
+   PrettyTable > 0.6
