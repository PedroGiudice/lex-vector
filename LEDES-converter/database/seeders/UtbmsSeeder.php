<?php

namespace Database\Seeders;

use App\Models\UtbmsActivityCode;
use App\Models\UtbmsTaskCode;
use Illuminate\Database\Seeder;

class UtbmsSeeder extends Seeder
{
    public function run(): void
    {
        $taskCodes = [
            ['code' => 'L100', 'description' => 'Case Assessment, Development and Administration'],
            ['code' => 'L110', 'description' => 'Fact Investigation/Development'],
            ['code' => 'L120', 'description' => 'Analysis/Strategy'],
            ['code' => 'L130', 'description' => 'Experts/Consultants'],
            ['code' => 'L140', 'description' => 'Document/File Management'],
            ['code' => 'L150', 'description' => 'Budgeting'],
            ['code' => 'L160', 'description' => 'Settlement/Non-Binding ADR'],
            ['code' => 'L190', 'description' => 'Other Case Assessment'],
            ['code' => 'L200', 'description' => 'Pre-Trial Pleadings and Motions'],
            ['code' => 'L210', 'description' => 'Pleadings'],
            ['code' => 'L220', 'description' => 'Preliminary Injunctions/Provisional Remedies'],
            ['code' => 'L230', 'description' => 'Court Mandated Conferences'],
            ['code' => 'L240', 'description' => 'Dispositive Motions'],
            ['code' => 'L250', 'description' => 'Other Written Motions and Submissions'],
            ['code' => 'L300', 'description' => 'Discovery'],
            ['code' => 'L310', 'description' => 'Written Discovery'],
            ['code' => 'L320', 'description' => 'Document Production'],
            ['code' => 'L330', 'description' => 'Depositions'],
            ['code' => 'L340', 'description' => 'Expert Discovery'],
            ['code' => 'L350', 'description' => 'Discovery Motions'],
            ['code' => 'L390', 'description' => 'Other Discovery'],
            ['code' => 'L400', 'description' => 'Trial Preparation and Trial'],
            ['code' => 'L410', 'description' => 'Fact Witnesses'],
            ['code' => 'L420', 'description' => 'Expert Witnesses'],
            ['code' => 'L430', 'description' => 'Written Motions and Submissions'],
            ['code' => 'L440', 'description' => 'Other Trial Preparation and Support'],
            ['code' => 'L450', 'description' => 'Trial and Hearing Attendance'],
            ['code' => 'L460', 'description' => 'Post-Trial Motions and Submissions'],
            ['code' => 'L500', 'description' => 'Appeal'],
            ['code' => 'L510', 'description' => 'Appellate Proceedings'],
            ['code' => 'L520', 'description' => 'Appeals to Courts of Superior Jurisdiction'],
        ];

        foreach ($taskCodes as $code) {
            UtbmsTaskCode::query()->updateOrCreate(
                ['code' => $code['code']],
                ['description' => $code['description']]
            );
        }

        $activityCodes = [
            ['code' => 'A101', 'description' => 'Plan and Prepare For'],
            ['code' => 'A102', 'description' => 'Research'],
            ['code' => 'A103', 'description' => 'Draft/Revise'],
            ['code' => 'A104', 'description' => 'Review/Analyze'],
            ['code' => 'A105', 'description' => 'Appear For/Attend'],
            ['code' => 'A106', 'description' => 'Communicate (with client, in writing)'],
            ['code' => 'A107', 'description' => 'Communicate (with client, verbally)'],
            ['code' => 'A108', 'description' => 'Communicate (other outside counsel)'],
            ['code' => 'A109', 'description' => 'Communicate (opposing counsel)'],
            ['code' => 'A110', 'description' => 'Communicate (court/agency)'],
            ['code' => 'A111', 'description' => 'Communicate (witnesses)'],
            ['code' => 'A112', 'description' => 'Communicate (other external)'],
            ['code' => 'A113', 'description' => 'Communicate (internal)'],
            ['code' => 'A114', 'description' => 'Manage Data/Files/Records'],
            ['code' => 'A115', 'description' => 'Manage Budget/Finances'],
            ['code' => 'A116', 'description' => 'Travel'],
            ['code' => 'A117', 'description' => 'Inspect/Examine'],
            ['code' => 'A118', 'description' => 'Negotiate'],
            ['code' => 'A119', 'description' => 'Other'],
        ];

        foreach ($activityCodes as $code) {
            UtbmsActivityCode::query()->updateOrCreate(
                ['code' => $code['code']],
                ['description' => $code['description']]
            );
        }
    }
}
