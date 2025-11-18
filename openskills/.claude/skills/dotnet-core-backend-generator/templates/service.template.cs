using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace Backend.Application.Services
{
    public class {{EntityName}}Service : I{{EntityName}}Service
    {
        private readonly I{{EntityName}}Repository _repository;
        private readonly IMapper _mapper;
        private readonly ILogger<{{EntityName}}Service> _logger;

        public {{EntityName}}Service(I{{EntityName}}Repository repository, IMapper mapper, ILogger<{{EntityName}}Service> logger)
        {
            _repository = repository;
            _mapper = mapper;
            _logger = logger;
        }

        public async Task<Result<{{EntityName}}ResponseDto>> GetByIdAsync(int id, CancellationToken cancellationToken = default)
        {
            try
            {
                var entity = await _repository.GetByIdAsync(id, cancellationToken);
                if (entity == null) return Result<{{EntityName}}ResponseDto>.Failure("Not found");
                var dto = _mapper.Map<{{EntityName}}ResponseDto>(entity);
                return Result<{{EntityName}}ResponseDto>.Success(dto);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in GetByIdAsync");
                return Result<{{EntityName}}ResponseDto>.Failure("An error occurred");
            }
        }

        // Implement Create, Update, Delete, GetAll following same patterns
    }
}
