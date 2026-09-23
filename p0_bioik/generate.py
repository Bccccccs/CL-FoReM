"""Build a separate instrumented plugin from pinned, unmodified local BioIK.
The generated source retains the upstream BSD notices. No upstream file is edited.
"""
import hashlib
from pathlib import Path
import sys


def replace_once(text,old,new):
    if text.count(old)!=1:raise RuntimeError('Unexpected upstream source: '+old[:100])
    return text.replace(old,new,1)


def generate(upstream,output):
    upstream,output=Path(upstream),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    plugin=(upstream/'kinematics_plugin.cpp').read_text()
    start=plugin.index('// implement BioIKKinematicsQueryOptions')
    end=plugin.index('// BioIK Kinematics Plugin',start)
    plugin=plugin[:start]+'''// Share the original library's query-options registry with RobotEnv.
namespace bio_ik {
const BioIKKinematicsQueryOptions *toBioIKKinematicsQueryOptions(const void *ptr);
}

'''+plugin[end:]
    plugin=plugin.replace('bio_ik_kinematics_plugin','p0_bio_ik_kinematics_plugin')
    plugin=plugin.replace('IKParallel','P0IKParallel').replace('"ik_parallel.h"','"p0_ik_parallel.h"')
    parallel=(upstream/'ik_parallel.h').read_text()
    parallel=parallel.replace('IKParallel','P0IKParallel').replace('ParallelExecutor','P0ParallelExecutor')
    parallel=replace_once(parallel,'#include "ik_base.h"','#include "ik_base.h"\n#include <fstream>\n#include <iomanip>\n#include <cstdlib>\n#include <unistd.h>')
    parallel=replace_once(parallel,'    bool enable_counter;','''    bool enable_counter;
    int p0_limit = 0;
    std::atomic<size_t> p0_steps{0};
    size_t p0_calls = 0;
    std::ofstream p0_trace;''')
    parallel=replace_once(parallel,'        enable_counter = params.enable_counter;','''        enable_counter = params.enable_counter;
        if(const char* v = std::getenv("P0_BIOIK_MAX_ITERATIONS")) p0_limit = std::stoi(v);
        if(p0_limit < 0) throw std::runtime_error("Negative P0 BioIK iteration budget");
        if(const char* v = std::getenv("P0_IK_TRACE")) {
            p0_trace.open(std::string(v) + "." + std::to_string(getpid()) + ".jsonl", std::ios::app);
            if(!p0_trace) throw std::runtime_error("Cannot open P0 IK trace");
        }''')
    parallel=replace_once(parallel,'        // init buffers','''        if(p0_limit && thread_count != 1)
            throw std::runtime_error("Fixed P0 BioIK budget requires one solver thread");
        // init buffers''')
    parallel=replace_once(parallel,'(ros::WallTime::now().toSec() < timeout && finished == 0) || (iteration == 0 && i == 0)',
        '((p0_limit ? iteration < size_t(p0_limit) : ros::WallTime::now().toSec() < timeout) && finished == 0) || (iteration == 0 && i == 0)')
    parallel=replace_once(parallel,'            solvers[i]->step();','            solvers[i]->step();\n            p0_steps++;')
    parallel=replace_once(parallel,'if(ros::WallTime::now().toSec() < timeout && finished == 0) solvers[i]->step();',
        'if((p0_limit || ros::WallTime::now().toSec() < timeout) && finished == 0) { solvers[i]->step(); p0_steps++; }')
    parallel=replace_once(parallel,'        iteration_count = 0;','        const double p0_start = ros::WallTime::now().toSec();\n        p0_steps = 0;\n        iteration_count = 0;')
    parallel=replace_once(parallel,'        success = solver_success[best_index];','''        success = solver_success[best_index];
        if(p0_trace) {
            p0_trace << std::setprecision(17) << "{\\"call\\":" << p0_calls++
              << ",\\"limit\\":" << p0_limit << ",\\"iterations\\":" << iteration_count.load()
              << ",\\"steps\\":" << p0_steps.load() << ",\\"success\\":" << (success ? "true" : "false")
              << ",\\"exit\\":\\"" << (success ? "success" : (p0_limit ? "iteration_budget" : "wall_budget"))
              << "\\",\\"seconds\\":" << ros::WallTime::now().toSec()-p0_start << "}\\n";
            p0_trace.flush();
        }''')
    (output/'p0_kinematics_plugin.cpp').write_text(plugin)
    (output/'p0_ik_parallel.h').write_text(parallel)
    (output/'upstream.sha256').write_text('\n'.join(hashlib.sha256((upstream/n).read_bytes()).hexdigest()+'  '+n for n in ['kinematics_plugin.cpp','ik_parallel.h']))


if __name__=='__main__':generate(*sys.argv[1:])
